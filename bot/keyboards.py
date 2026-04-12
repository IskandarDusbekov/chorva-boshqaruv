from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from django.conf import settings


def main_menu_keyboard(role):
    if role in {"admin", "manager"}:
        buttons = [
            [KeyboardButton(text="Default pulni olish")],
            [KeyboardButton(text="\U0001F4DD Kiritish"), KeyboardButton(text="\U0001F4CA Hisobotlar")],
            [KeyboardButton(text="\U0001F310 Saytga o'tish"), KeyboardButton(text="\U0001F6E1\uFE0F Mini App")],
        ]
    else:
        buttons = [
            [KeyboardButton(text="\U0001F4DD Kiritish")],
            [KeyboardButton(text="\U0001F310 Saytga o'tish")],
        ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def mini_app_inline_keyboard(role):
    base_url = settings.SITE_BASE_URL.rstrip("/")
    if role not in {"admin", "manager"} or not base_url.startswith("https://"):
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\U0001F6E1\uFE0F Mini Appni ochish",
                    web_app=WebAppInfo(url=f"{base_url}/auth/telegram-mini-app/"),
                )
            ]
        ]
    )


def entry_menu_keyboard(role="admin"):
    if role in {"admin", "manager"}:
        keyboard = [
            [KeyboardButton(text="\U0001F95B Sut kiritish"), KeyboardButton(text="\U0001F4B0 Kirim kiritish")],
            [KeyboardButton(text="\U0001F4B8 Chiqim kiritish")],
        ]
    else:
        keyboard = [
            [KeyboardButton(text="\U0001F4B0 Kirim kiritish"), KeyboardButton(text="\U0001F4B8 Chiqim kiritish")],
        ]
    keyboard.append([KeyboardButton(text="\u2B05\uFE0F Orqaga"), KeyboardButton(text="\U0001F3E0 Bosh menyu")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def shift_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="\U0001F305 Ertalabki"), KeyboardButton(text="\U0001F307 Kunduzgi / kechki")],
            [KeyboardButton(text="\u2B05\uFE0F Orqaga"), KeyboardButton(text="\U0001F3E0 Bosh menyu")],
        ],
        resize_keyboard=True,
    )


def finance_currency_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="UZS"), KeyboardButton(text="USD")],
            [KeyboardButton(text="\u2B05\uFE0F Orqaga"), KeyboardButton(text="\U0001F3E0 Bosh menyu")],
        ],
        resize_keyboard=True,
    )


def finance_source_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="\U0001F3E6 Ichki hisob"), KeyboardButton(text="\U0001F4BC Tashqi hisob")],
            [KeyboardButton(text="\u2B05\uFE0F Orqaga"), KeyboardButton(text="\U0001F3E0 Bosh menyu")],
        ],
        resize_keyboard=True,
    )


def quick_date_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="\U0001F4C5 Bugun")],
            [KeyboardButton(text="\u2B05\uFE0F Orqaga"), KeyboardButton(text="\U0001F3E0 Bosh menyu")],
        ],
        resize_keyboard=True,
    )


def skip_note_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="\u23ED\uFE0F Izohsiz saqlash")],
            [KeyboardButton(text="\u2B05\uFE0F Orqaga"), KeyboardButton(text="\U0001F3E0 Bosh menyu")],
        ],
        resize_keyboard=True,
    )
