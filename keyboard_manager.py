from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def gen_keyboard(button_rows):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for row_data in button_rows:
        row = []
        for button_name in row_data:
            match button_name:
                case "voices":
                    row.append(InlineKeyboardButton(text="Мои голоса", callback_data="voices"))
                case "new_voice":
                    row.append(InlineKeyboardButton(text="Создать голос", callback_data="new_voice"))
                case "delete_voice":
                    row.append(InlineKeyboardButton(text="Удалить голос", callback_data="delete_voice"))
                case "tts":
                    row.append(InlineKeyboardButton(text="Озвучить текст (Выбрать голос)", callback_data="tts"))
                case "menu":
                    row.append(InlineKeyboardButton(text="Главное меню", callback_data="menu"))
                case "new_voice_next__name":
                    row.append(InlineKeyboardButton(text="Продолжить", callback_data="new_voice_next__name"))
                case "cancel":
                    row.append(InlineKeyboardButton(text="Отменить", callback_data="cancel"))
                case "ok":
                    row.append(InlineKeyboardButton(text="Подтвердить", callback_data="ok"))
        if row:  # Don't add empty rows
            keyboard.inline_keyboard.append(row)

    return keyboard


def get_main_keyboard():
    keyboard = gen_keyboard(
        [
            ["voices", "new_voice"],
            ["tts"]
        ]
    )
    return keyboard
