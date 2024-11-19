# Обработчик команд
from aiogram.filters import Command, Filter
from aiogram.types import Message

import keyboard_manager as km
import utils
from messages import messages


def init_bot_commands(bot, dp, database):
    @dp.message(Command("start"))
    async def start(message: Message) -> None:
        database.set_bot_waiting_for(message.from_user.id, "")
        print(f"start!")
        database.register_user(message.from_user.id)
        kolobok = "CAACAgIAAxkBAAIEV2co-1yqRTVgq3irFP4Bo7qVRFQiAAJyAQACIjeOBPAcpJFtEi86NgQ"
        await bot.send_sticker(message.from_user.id, kolobok)
        await message.answer(messages["start_message"], reply_markup=km.get_main_keyboard())

    @dp.message(Command("help"))
    async def help(message: Message) -> None:
        if await utils.check_user_login(bot, message):
            await message.answer("тест")
