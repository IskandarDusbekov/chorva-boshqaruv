from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from django.conf import settings


def main_menu_keyboard(role):
    base_url = settings.SITE_BASE_URL.rstrip("/")
    buttons = [
        [KeyboardButton(text="Default pulni olish")],
        [KeyboardButton(text="📝 Kiritish"), KeyboardButton(text="📊 Hisobotlar")],
        [KeyboardButton(text="🌐 Saytga o'tish")],
    ]
    if role in {"admin", "manager"} and base_url.startswith("https://"):
        buttons.insert(
            1,
            [
                KeyboardButton(
                    text="🛡️ Mini Appni ochish",
                    web_app=WebAppInfo(url=f"{base_url}/auth/telegram-mini-app/"),
                )
            ],
        )
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def entry_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🥛 Sut kiritish"), KeyboardButton(text="💰 Kirim kiritish")],
            [KeyboardButton(text="💸 Chiqim kiritish")],
            [KeyboardButton(text="⬅️ Orqaga"), KeyboardButton(text="🏠 Bosh menyu")],
        ],
        resize_keyboard=True,
    )


def shift_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌅 Ertalabki"), KeyboardButton(text="🌇 Kunduzgi / kechki")],
            [KeyboardButton(text="⬅️ Orqaga"), KeyboardButton(text="🏠 Bosh menyu")],
        ],
        resize_keyboard=True,
    )


def finance_currency_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="UZS"), KeyboardButton(text="USD")],
            [KeyboardButton(text="⬅️ Orqaga"), KeyboardButton(text="🏠 Bosh menyu")],
        ],
        resize_keyboard=True,
    )


def finance_source_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏦 Ichki hisob"), KeyboardButton(text="💼 Tashqi hisob")],
            [KeyboardButton(text="⬅️ Orqaga"), KeyboardButton(text="🏠 Bosh menyu")],
        ],
        resize_keyboard=True,
    )


def quick_date_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Bugun")],
            [KeyboardButton(text="⬅️ Orqaga"), KeyboardButton(text="🏠 Bosh menyu")],
        ],
        resize_keyboard=True,
    )


def skip_note_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏭️ Izohsiz saqlash")],
            [KeyboardButton(text="⬅️ Orqaga"), KeyboardButton(text="🏠 Bosh menyu")],
        ],
        resize_keyboard=True,
    )
