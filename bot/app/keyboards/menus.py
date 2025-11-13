from __future__ import annotations

from telegram import KeyboardButton, ReplyKeyboardMarkup


def build_contact_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Поделиться номером", request_contact=True)],
            [KeyboardButton(text="Отмена")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def build_skip_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
            [KeyboardButton(text="Отмена")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def build_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отмена")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def build_main_menu_keyboard(is_subscriber: bool) -> ReplyKeyboardMarkup:
    if is_subscriber:
        keyboard = [
            [KeyboardButton(text="Мои каналы"), KeyboardButton(text="Продлить подписку")],
            [KeyboardButton(text="История платежей"), KeyboardButton(text="Статус")],
            [KeyboardButton(text="Помощь")],
        ]
    else:
        keyboard = [
            [KeyboardButton(text="Купить подписку")],
            [KeyboardButton(text="История платежей"), KeyboardButton(text="Статус")],
            [KeyboardButton(text="Помощь")],
        ]

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=False)

