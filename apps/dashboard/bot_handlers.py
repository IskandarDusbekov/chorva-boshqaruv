from datetime import timedelta
from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, Message, ReplyKeyboardMarkup
from asgiref.sync import sync_to_async
from django.conf import settings
from django.utils import timezone

from apps.accounts.selectors import get_user_by_telegram_id
from apps.accounts.services import create_audit_log, generate_access_link, get_panel_target_path
from bot.keyboards import (
    entry_menu_keyboard,
    finance_currency_keyboard,
    finance_source_keyboard,
    main_menu_keyboard,
    mini_app_inline_keyboard,
    quick_date_keyboard,
    shift_keyboard,
    skip_note_keyboard,
)
from bot.states import QuickEntryStates

from .models import AccountSourceChoices, FinanceCategory, FinanceEntry, FinanceStatusChoices, FinanceTypeChoices
from .selectors import get_period_report, get_worker_payroll_summary
from .services import create_finance_entry, create_milk_income_from_record, create_milk_record, mark_milk_payment_received


router = Router(name="dashboard")


def _today():
    return timezone.now().date()


def reports_keyboard(role):
    rows = [
        [KeyboardButton(text="📅 Haftalik hisobot"), KeyboardButton(text="🗓️ Oylik hisobot")],
        [KeyboardButton(text="⏮️ Kechagi hisobot")],
    ]
    if role in {"admin", "manager"}:
        rows[1].append(KeyboardButton(text="👷 Ishchilar hisoboti"))
    rows.append([KeyboardButton(text="🌐 Saytga o'tish"), KeyboardButton(text="🏠 Bosh menyu")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


async def _safe_user(message: Message):
    return await sync_to_async(get_user_by_telegram_id)(message.from_user.id)


async def _return_main_menu(message: Message, state: FSMContext, text="🏠 Bosh menyuga qaytdingiz."):
    user = await _safe_user(message)
    await state.clear()
    if user:
        await message.answer(text, reply_markup=main_menu_keyboard(user.role))
        mini_app_keyboard = mini_app_inline_keyboard(user.role)
        if mini_app_keyboard:
            await message.answer(
                "Mini Appni shu inline tugma orqali oching. Telegram ma'lumoti shu yo'l bilan to'g'ri keladi.",
                reply_markup=mini_app_keyboard,
            )
    else:
        await message.answer(text)


def _parse_decimal(value: str):
    try:
        return Decimal(value.replace(" ", "").replace(",", "."))
    except (InvalidOperation, AttributeError):
        return None


def _parse_bot_date(value: str):
    today = _today()
    if value == "📅 Bugun":
        return today
    try:
        return timezone.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


async def _expense_categories_keyboard():
    categories = await sync_to_async(list)(
        FinanceCategory.objects.filter(is_active=True, entry_type=FinanceTypeChoices.EXPENSE).order_by("name")
    )
    rows = [[KeyboardButton(text=item.name)] for item in categories[:8]]
    rows.append([KeyboardButton(text="⬅️ Orqaga"), KeyboardButton(text="🏠 Bosh menyu")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True), {item.name for item in categories}


async def _income_categories_keyboard():
    categories = await sync_to_async(list)(
        FinanceCategory.objects.filter(is_active=True, entry_type=FinanceTypeChoices.INCOME).order_by("name")
    )
    rows = [[KeyboardButton(text=item.name)] for item in categories[:8]]
    rows.append([KeyboardButton(text="⬅️ Orqaga"), KeyboardButton(text="🏠 Bosh menyu")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True), {item.name for item in categories}


async def _build_report_message(period):
    today = _today()
    if period == "monthly":
        date_from = today - timedelta(days=30)
        title = "🗓️ Oxirgi 30 kunlik hisobot"
    elif period == "yesterday":
        date_from = today - timedelta(days=1)
        title = "⏮️ Kechagi hisobot"
    else:
        date_from = today - timedelta(days=6)
        title = "📅 Oxirgi 7 kunlik hisobot"

    report = await sync_to_async(get_period_report)(date_from, today)
    stats = report["overview"]
    return (
        f"{title}\n\n"
        f"🥛 Sut hajmi: {stats['total_liters']} litr\n"
        f"💰 Kirim: {stats['income_totals']['UZS']} UZS / {stats['income_totals']['USD']} USD\n"
        f"💸 Chiqim: {stats['expense_totals']['UZS']} UZS / {stats['expense_totals']['USD']} USD\n"
        f"🏦 Ichki balans: {stats['internal_balance']['UZS']} UZS / {stats['internal_balance']['USD']} USD\n"
        f"💼 Tashqi balans: {stats['external_balance']['UZS']} UZS / {stats['external_balance']['USD']} USD\n"
        f"⏳ Kutilayotgan sut puli: {stats['pending_milk_totals']['UZS']} UZS / {stats['pending_milk_totals']['USD']} USD\n"
        f"👷 Ishchilar soni: {stats['worker_count']}"
    )


def _pending_milk_payments():
    return list(
        FinanceEntry.objects.filter(
            status=FinanceStatusChoices.PENDING,
            related_milk_record__isnull=False,
        )
        .select_related("related_milk_record")
        .order_by("-entry_date", "-created_at")[:10]
    )


def _receive_pending_milk_to_internal(entry_id):
    pending_entry = FinanceEntry.objects.filter(
        id=entry_id,
        status=FinanceStatusChoices.PENDING,
        related_milk_record__isnull=False,
    ).first()
    if not pending_entry:
        return None
    return mark_milk_payment_received(
        entry_id=entry_id,
        account_source=AccountSourceChoices.INTERNAL,
        received_at=_today(),
    )

@router.message(F.text == "📊 Hisobotlar")
async def reports_menu(message: Message):
    user = await _safe_user(message)
    if not user or user.role not in {"admin", "manager"}:
        await message.answer("Bu bo'lim faqat admin va manager uchun.")
        return
    await message.answer("📊 Kerakli hisobot turini tanlang.", reply_markup=reports_keyboard(user.role))


@router.message(F.text == "Default pulni olish")
async def pending_milk_menu(message: Message):
    user = await _safe_user(message)
    if not user or not user.is_telegram_verified:
        await message.answer("Avval bot orqali tasdiqlanib oling.")
        return
    if user.role not in {"admin", "manager"}:
        await message.answer("Default sut puli bo'limi siz uchun yopiq.")
        return

    payments = await sync_to_async(_pending_milk_payments)()
    if not payments:
        await message.answer("Default hisobda olinadigan sut puli yo'q.")
        return

    rows = []
    lines = ["Default hisobdagi kutilayotgan sut pullari:"]
    for item in payments:
        liters = item.related_milk_record.total_liters if item.related_milk_record else 0
        lines.append(f"#{item.id} | {item.entry_date} | {liters} L | {item.amount} {item.currency}")
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"#{item.id} - {item.amount} {item.currency} ichki hisobga",
                    callback_data=f"milk_receive_internal:{item.id}",
                )
            ]
        )

    await message.answer(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


@router.callback_query(F.data.startswith("milk_receive_internal:"))
async def receive_pending_milk_callback(callback: CallbackQuery):
    user = await sync_to_async(get_user_by_telegram_id)(callback.from_user.id)
    if not user or not user.is_telegram_verified:
        await callback.answer("Avval tasdiqlaning.", show_alert=True)
        return

    entry_id = int(callback.data.split(":", 1)[1])
    entry = await sync_to_async(_receive_pending_milk_to_internal)(entry_id)
    if not entry:
        await callback.answer("Yozuv topilmadi yoki allaqachon o'tkazilgan.", show_alert=True)
        return
    await sync_to_async(create_audit_log)(
        user=user,
        action="milk_payment_received",
        object_type="FinanceEntry",
        object_id=str(entry.pk),
        meta={
            "amount": str(entry.amount),
            "currency": entry.currency,
            "source": entry.source,
            "received_at": str(entry.received_at),
            "via": "telegram_bot",
        },
    )

    await callback.message.edit_text(
        f"Pul ichki hisobga o'tkazildi.\n"
        f"Sana: {entry.entry_date}\n"
        f"Miqdor: {entry.amount} {entry.currency}\n"
        f"Holat: {entry.get_status_display()}"
    )
    await callback.answer("Ichki hisobga qo'shildi.")


@router.message(F.text == "📝 Kiritish")
async def entry_menu(message: Message, state: FSMContext):
    user = await _safe_user(message)
    if not user or not user.is_telegram_verified:
        await message.answer("Avval tasdiqlanib oling.")
        return
    await state.clear()
    await state.update_data(role=user.role)
    await state.set_state(QuickEntryStates.waiting_for_entry_type)
    await message.answer("📝 Tezkor kiritish turini tanlang.", reply_markup=entry_menu_keyboard(user.role))


@router.message(F.text.in_({"🛡️ Mini App", "Mini App"}))
async def open_mini_app_menu(message: Message):
    user = await _safe_user(message)
    if not user or not user.is_telegram_verified:
        await message.answer("Avval tasdiqlanib oling.")
        return
    mini_keyboard = mini_app_inline_keyboard(user.role)
    if not mini_keyboard:
        await message.answer("Mini App faqat admin va manager uchun ochiq.")
        return
    await message.answer(
        "Mini Appni xavfsiz inline tugma orqali oching.",
        reply_markup=mini_keyboard,
    )


@router.message(F.text == "🏠 Bosh menyu")
async def go_main_menu(message: Message, state: FSMContext):
    await _return_main_menu(message, state)


@router.message(F.text == "⬅️ Orqaga")
async def go_back_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if not current_state:
        await _return_main_menu(message, state)
        return
    data = await state.get_data()
    if current_state in {QuickEntryStates.waiting_for_entry_type.state, QuickEntryStates.waiting_for_shift.state}:
        await state.set_state(QuickEntryStates.waiting_for_entry_type)
        await message.answer("📝 Kiritish turini tanlang.", reply_markup=entry_menu_keyboard(data.get("role", "admin")))
        return

    entry_type = data.get("entry_type")

    if current_state == QuickEntryStates.waiting_for_record_date.state:
        if entry_type == "milk":
            await state.set_state(QuickEntryStates.waiting_for_shift)
            await message.answer("🕒 Qaysi paytdagi sut?", reply_markup=shift_keyboard())
        else:
            await state.set_state(QuickEntryStates.waiting_for_entry_type)
            await message.answer("📝 Kiritish turini tanlang.", reply_markup=entry_menu_keyboard(data.get("role", "admin")))
        return

    if current_state == QuickEntryStates.waiting_for_liters.state:
        await state.set_state(QuickEntryStates.waiting_for_record_date)
        await message.answer("📅 Sanani kiriting (`YYYY-MM-DD`) yoki `Bugun` ni tanlang.", reply_markup=quick_date_keyboard())
        return

    if current_state == QuickEntryStates.waiting_for_finance_category.state:
        await state.set_state(QuickEntryStates.waiting_for_entry_type)
        await message.answer("📝 Kiritish turini tanlang.", reply_markup=entry_menu_keyboard(data.get("role", "admin")))
        return

    if current_state == QuickEntryStates.waiting_for_finance_amount.state:
        await state.set_state(QuickEntryStates.waiting_for_finance_category)
        keyboard, _choices = await (_income_categories_keyboard() if entry_type == "income" else _expense_categories_keyboard())
        await message.answer("🏷️ Kategoriyani qayta tanlang.", reply_markup=keyboard)
        return

    if current_state == QuickEntryStates.waiting_for_finance_currency.state:
        await state.set_state(QuickEntryStates.waiting_for_finance_amount)
        await message.answer(
            "💵 Miqdorni kiriting. Masalan: `1000000`",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⬅️ Orqaga"), KeyboardButton(text="🏠 Bosh menyu")]],
                resize_keyboard=True,
            ),
        )
        return

    if current_state == QuickEntryStates.waiting_for_finance_source.state:
        await state.set_state(QuickEntryStates.waiting_for_finance_currency)
        await message.answer("💱 Valyutani tanlang.", reply_markup=finance_currency_keyboard())
        return

    if current_state == QuickEntryStates.waiting_for_finance_note.state:
        await state.set_state(QuickEntryStates.waiting_for_record_date)
        await message.answer("📅 Sanani kiriting (`YYYY-MM-DD`) yoki `Bugun` ni tanlang.", reply_markup=quick_date_keyboard())
        return

    await _return_main_menu(message, state)


@router.message(QuickEntryStates.waiting_for_entry_type, F.text.in_({"🥛 Sut kiritish", "💰 Kirim kiritish", "💸 Chiqim kiritish"}))
async def choose_entry_type(message: Message, state: FSMContext):
    data = await state.get_data()
    role = data.get("role", "admin")
    if role == "user" and message.text == "🥛 Sut kiritish":
        await message.answer("Oddiy foydalanuvchi sut bo'limiga kira olmaydi.", reply_markup=entry_menu_keyboard(role))
        return
    if message.text == "🥛 Sut kiritish":
        await state.update_data(entry_type="milk")
        await state.set_state(QuickEntryStates.waiting_for_shift)
        await message.answer("🕒 Qaysi paytdagi sut?", reply_markup=shift_keyboard())
        return

    if message.text == "💰 Kirim kiritish":
        await state.update_data(entry_type="income")
        keyboard, _choices = await _income_categories_keyboard()
        await state.set_state(QuickEntryStates.waiting_for_finance_category)
        await message.answer("🏷️ Kirim kategoriyasini tanlang.", reply_markup=keyboard)
        return

    await state.update_data(entry_type="expense")
    keyboard, _choices = await _expense_categories_keyboard()
    await state.set_state(QuickEntryStates.waiting_for_finance_category)
    await message.answer("🏷️ Chiqim kategoriyasini tanlang.", reply_markup=keyboard)


@router.message(QuickEntryStates.waiting_for_shift, F.text.in_({"🌅 Ertalabki", "🌇 Kunduzgi / kechki"}))
async def choose_shift(message: Message, state: FSMContext):
    shift = "morning" if message.text == "🌅 Ertalabki" else "evening"
    await state.update_data(shift=shift)
    await state.set_state(QuickEntryStates.waiting_for_record_date)
    await message.answer("📅 Sanani kiriting (`YYYY-MM-DD`) yoki `Bugun` ni tanlang.", reply_markup=quick_date_keyboard())


@router.message(QuickEntryStates.waiting_for_record_date)
async def choose_record_date(message: Message, state: FSMContext):
    value = _parse_bot_date((message.text or "").strip())
    if not value:
        await message.answer("❗ Sana noto'g'ri. Masalan: `2026-04-09` yoki `Bugun`.", reply_markup=quick_date_keyboard())
        return

    await state.update_data(record_date=value)
    data = await state.get_data()
    if data.get("entry_type") == "milk":
        await state.set_state(QuickEntryStates.waiting_for_liters)
        await message.answer("🥛 Litrni kiriting. Masalan: `245.5`")
    else:
        await state.set_state(QuickEntryStates.waiting_for_finance_note)
        await message.answer("🧾 Izoh kiriting yoki `Izohsiz saqlash` ni bosing.", reply_markup=skip_note_keyboard())


@router.message(QuickEntryStates.waiting_for_liters)
async def save_milk_entry(message: Message, state: FSMContext):
    liters = _parse_decimal((message.text or "").strip())
    if liters is None:
        await message.answer("❗ Litr noto'g'ri. Masalan: `245.5`")
        return

    data = await state.get_data()
    user = await _safe_user(message)
    milk_record = await sync_to_async(create_milk_record)(
        user=user,
        record_date=data["record_date"],
        shift=data["shift"],
        liters=liters,
        note="Bot orqali tezkor kiritildi",
    )
    pending_entry = await sync_to_async(create_milk_income_from_record)(user=user, milk_record=milk_record)
    await sync_to_async(create_audit_log)(
        user=user,
        action="milk_record_created",
        object_type="MilkRecord",
        object_id=str(milk_record.pk),
        meta={
            "date": str(milk_record.record_date),
            "liters": str(milk_record.total_liters),
            "via": "telegram_bot",
        },
    )
    shift_name = "ertalabki" if data["shift"] == "morning" else "kunduzgi / kechki"
    await _return_main_menu(
        message,
        state,
        f"✅ Sut saqlandi.\n📅 Sana: {data['record_date']}\n🕒 Payt: {shift_name}\n🥛 Litr: {liters}\n💰 Kutilayotgan to'lov: {pending_entry.amount} {pending_entry.currency}",
    )


@router.message(QuickEntryStates.waiting_for_finance_category)
async def choose_finance_category(message: Message, state: FSMContext):
    data = await state.get_data()
    entry_type = data.get("entry_type")
    keyboard, choices = await (_income_categories_keyboard() if entry_type == "income" else _expense_categories_keyboard())
    if message.text not in choices:
        await message.answer("🏷️ Kategoriyani tugmadan tanlang.", reply_markup=keyboard)
        return

    await state.update_data(category=message.text)
    await state.set_state(QuickEntryStates.waiting_for_finance_amount)
    await message.answer("💵 Miqdorni kiriting. Masalan: `1000000`")


@router.message(QuickEntryStates.waiting_for_finance_amount)
async def choose_finance_amount(message: Message, state: FSMContext):
    amount = _parse_decimal((message.text or "").strip())
    if amount is None:
        await message.answer("❗ Miqdor noto'g'ri. Masalan: `1000000`")
        return

    await state.update_data(amount=amount)
    await state.set_state(QuickEntryStates.waiting_for_finance_currency)
    await message.answer("💱 Valyutani tanlang.", reply_markup=finance_currency_keyboard())


@router.message(QuickEntryStates.waiting_for_finance_currency, F.text.in_({"UZS", "USD"}))
async def choose_finance_currency(message: Message, state: FSMContext):
    await state.update_data(currency=message.text)
    await state.set_state(QuickEntryStates.waiting_for_finance_source)
    await message.answer("🏦 Qaysi hisobdan yoki hisobga?", reply_markup=finance_source_keyboard())


@router.message(QuickEntryStates.waiting_for_finance_source, F.text.in_({"🏦 Ichki hisob", "💼 Tashqi hisob"}))
async def choose_finance_source(message: Message, state: FSMContext):
    source = AccountSourceChoices.INTERNAL if message.text == "🏦 Ichki hisob" else AccountSourceChoices.EXTERNAL
    await state.update_data(source=source)
    await state.set_state(QuickEntryStates.waiting_for_record_date)
    await message.answer("📅 Sanani kiriting (`YYYY-MM-DD`) yoki `Bugun` ni tanlang.", reply_markup=quick_date_keyboard())


@router.message(QuickEntryStates.waiting_for_finance_note)
async def save_finance_entry(message: Message, state: FSMContext):
    data = await state.get_data()
    note = "" if message.text == "⏭️ Izohsiz saqlash" else (message.text or "").strip()
    user = await _safe_user(message)
    entry = await sync_to_async(create_finance_entry)(
        user=user,
        entry_type=data["entry_type"],
        category=data["category"],
        amount=data["amount"],
        currency=data["currency"],
        source=data["source"],
        entry_date=data["record_date"],
        note=note,
    )
    await sync_to_async(create_audit_log)(
        user=user,
        action="finance_entry_created",
        object_type="FinanceEntry",
        object_id=str(entry.pk),
        meta={
            "type": entry.entry_type,
            "category": entry.category,
            "amount": str(entry.amount),
            "currency": entry.currency,
            "via": "telegram_bot",
        },
    )
    entry_type_name = "Kirim" if entry.entry_type == FinanceTypeChoices.INCOME else "Chiqim"
    source_name = "Ichki hisob" if entry.source == AccountSourceChoices.INTERNAL else "Tashqi hisob"
    await _return_main_menu(
        message,
        state,
        f"✅ {entry_type_name} saqlandi.\n🏷️ Kategoriya: {entry.category}\n💵 Miqdor: {entry.amount} {entry.currency}\n🏦 Hisob: {source_name}\n📅 Sana: {entry.entry_date}",
    )


@router.message(F.text.in_({"📅 Haftalik hisobot", "🗓️ Oylik hisobot", "⏮️ Kechagi hisobot"}))
async def send_period_report(message: Message):
    period_map = {
        "📅 Haftalik hisobot": "weekly",
        "🗓️ Oylik hisobot": "monthly",
        "⏮️ Kechagi hisobot": "yesterday",
    }
    text = await _build_report_message(period_map[message.text])
    await message.answer(text)


@router.message(F.text == "👷 Ishchilar hisoboti")
async def send_worker_report(message: Message):
    user = await _safe_user(message)
    if not user or user.role not in {"admin", "manager"}:
        await message.answer("Ishchilar hisobotini faqat admin yoki manager oladi.")
        return
    payroll = await sync_to_async(get_worker_payroll_summary)()
    if not payroll:
        await message.answer("👷 Ishchilar hali kiritilmagan.")
        return

    lines = ["👷 Ishchilar hisoboti"]
    for item in payroll:
        lines.append(
            f"👤 {item['name']} | {item['role']}\n"
            f"💼 Oylik: {item['salary']} {item['currency']}\n"
            f"💰 Shu oy UZS: {item['month_paid_uzs']} | USD: {item['month_paid_usd']}\n"
            f"📉 Qolgan: {item['remaining']} {item['currency']}"
        )
    await message.answer("\n\n".join(lines))


@router.message(F.text.in_({"🌐 Saytga o'tish", "Saytga o'tish", "Panelni ochish"}))
async def open_panel(message: Message):
    user = await sync_to_async(get_user_by_telegram_id)(message.from_user.id)
    if not user or not user.is_telegram_verified:
        await message.answer("❗ Avval bot orqali tasdiqlanib oling.")
        return

    access_link = await sync_to_async(generate_access_link)(
        user=user,
        target_path=get_panel_target_path(user),
        created_by_bot=True,
    )
    base_url = settings.SITE_BASE_URL.rstrip("/")
    url = f"{base_url}/panel/open/#token={access_link.token}"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🌐 Saytga o'tish", url=url)]])
    await message.answer(
        "🔐 Vaqtinchalik havola tayyor.\nBu havola bir marta ishlaydi va qisqa vaqtdan keyin eskiradi.",
        reply_markup=keyboard,
    )


@router.message(QuickEntryStates.waiting_for_entry_type)
async def invalid_entry_type(message: Message):
    user = await _safe_user(message)
    role = user.role if user else "admin"
    await message.answer("📝 Tugmalardan birini tanlang.", reply_markup=entry_menu_keyboard(role))


@router.message(QuickEntryStates.waiting_for_finance_currency)
async def invalid_currency(message: Message):
    await message.answer("💱 Valyutani tugmadan tanlang.", reply_markup=finance_currency_keyboard())


@router.message(QuickEntryStates.waiting_for_finance_source)
async def invalid_source(message: Message):
    await message.answer("🏦 Hisob turini tugmadan tanlang.", reply_markup=finance_source_keyboard())
