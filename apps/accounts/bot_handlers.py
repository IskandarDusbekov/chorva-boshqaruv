from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from asgiref.sync import sync_to_async
from django.core.exceptions import PermissionDenied

from bot.keyboards import main_menu_keyboard, mini_app_inline_keyboard
from bot.states import LoginStates

from .services import (
    authenticate_first_login,
    check_whitelist,
    get_login_lock_remaining,
    register_failed_login_attempt,
    reset_failed_login_attempts,
)
from .selectors import get_user_by_telegram_id
from .utils import normalize_phone_number


router = Router(name="accounts")


def contact_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Kontakt yuborish", request_contact=True)]],
        resize_keyboard=True,
    )


async def _send_verified_main_menu(message: Message, user, text: str):
    await message.answer(text, reply_markup=main_menu_keyboard(user.role))
    mini_app_keyboard = mini_app_inline_keyboard(user.role)
    if mini_app_keyboard:
        await message.answer(
            "Mini Appni shu inline tugma orqali oching. Telegram ma'lumoti shu yo'l bilan to'g'ri keladi.",
            reply_markup=mini_app_keyboard,
        )


async def restart_auth_flow(message: Message, state: FSMContext, text):
    await state.clear()
    await state.set_state(LoginStates.waiting_for_contact)
    await message.answer(text, reply_markup=contact_keyboard())


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    lock_remaining = await sync_to_async(get_login_lock_remaining)(message.from_user.id)
    if lock_remaining > 0:
        minutes = max(1, (lock_remaining + 59) // 60)
        await state.clear()
        await message.answer(
            f"Siz 3 marta noto'g'ri kiritdingiz. {minutes} daqiqadan keyin qayta urinib ko'ring."
        )
        return

    user = await sync_to_async(get_user_by_telegram_id)(message.from_user.id)
    if user and user.is_telegram_verified:
        await state.clear()
        await _send_verified_main_menu(
            message,
            user,
            "Assalomu alaykum. Siz tasdiqlangansiz, menyudan davom eting.",
        )
        return

    await state.set_state(LoginStates.waiting_for_contact)
    await message.answer("Davom etish uchun telefon raqamingizni yuboring.", reply_markup=contact_keyboard())


@router.message(LoginStates.waiting_for_contact, F.contact)
async def contact_handler(message: Message, state: FSMContext):
    lock_remaining = await sync_to_async(get_login_lock_remaining)(message.from_user.id)
    if lock_remaining > 0:
        minutes = max(1, (lock_remaining + 59) // 60)
        await state.clear()
        await message.answer(
            f"Siz vaqtincha bloklangansiz. {minutes} daqiqadan keyin qayta urinib ko'ring."
        )
        return

    contact = message.contact
    if not contact:
        await message.answer("Kontakt topilmadi. Qayta yuboring.")
        return

    if contact.user_id and contact.user_id != message.from_user.id:
        await message.answer("Iltimos, o'zingizning kontaktingizni yuboring.")
        return

    phone_number = normalize_phone_number(contact.phone_number)
    allowed_contact = await sync_to_async(check_whitelist)(phone_number)
    if not allowed_contact:
        await message.answer("Sizga hali ruxsat berilmagan. Admin bilan bog'laning.")
        return

    await state.update_data(phone_number=phone_number, role=allowed_contact.role)
    await state.set_state(LoginStates.waiting_for_username)
    await message.answer(
        "Ruxsat topildi.\nEndi admin sizga bergan username ni kiriting."
    )


@router.message(LoginStates.waiting_for_contact)
async def contact_prompt_handler(message: Message):
    await message.answer("Davom etish uchun pastdagi tugma orqali kontakt yuboring.")


@router.message(LoginStates.waiting_for_username)
async def username_handler(message: Message, state: FSMContext):
    username = (message.text or "").strip()
    if not username:
        await message.answer("Username bo'sh bo'lmasin. Qayta kiriting.")
        return

    await state.update_data(username=username)
    await state.set_state(LoginStates.waiting_for_password)
    await message.answer("Parolni kiriting.")


@router.message(LoginStates.waiting_for_password)
async def password_handler(message: Message, state: FSMContext):
    lock_remaining = await sync_to_async(get_login_lock_remaining)(message.from_user.id)
    if lock_remaining > 0:
        minutes = max(1, (lock_remaining + 59) // 60)
        await state.clear()
        await message.answer(
            f"Siz vaqtincha bloklangansiz. {minutes} daqiqadan keyin qayta urinib ko'ring."
        )
        return

    password = (message.text or "").strip()
    if not password:
        await message.answer("Parol bo'sh bo'lmasin. Qayta kiriting.")
        return

    data = await state.get_data()
    username = data.get("username")
    phone_number = data.get("phone_number", "")

    try:
        user, _session = await sync_to_async(authenticate_first_login)(
            username=username,
            password=password,
            phone_number=phone_number,
            telegram_id=message.from_user.id,
            chat_id=message.chat.id,
            device_note="telegram_bot",
        )
    except PermissionDenied as exc:
        attempts, lock_seconds = await sync_to_async(register_failed_login_attempt)(message.from_user.id)
        if lock_seconds:
            minutes = max(1, lock_seconds // 60)
            await restart_auth_flow(
                message,
                state,
                f"{exc}\n3 marta noto'g'ri urinish bo'ldi. {minutes} daqiqaga bloklandiz.",
            )
            return
        await restart_auth_flow(
            message,
            state,
            f"{exc}\nQayta urinib ko'rish uchun boshidan kontakt yuboring. Qolgan urinishlar: {3 - attempts}",
        )
        return
    except Exception:
        await restart_auth_flow(
            message,
            state,
            "Kirish vaqtida xatolik yuz berdi. Qayta urinib ko'rish uchun boshidan kontakt yuboring.",
        )
        return

    await sync_to_async(reset_failed_login_attempts)(message.from_user.id)
    await state.clear()
    await _send_verified_main_menu(
        message,
        user,
        f"Xush kelibsiz, {user.full_name}. Telegram akkauntingiz muvaffaqiyatli bog'landi.",
    )
