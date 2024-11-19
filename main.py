from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from aiogram import Bot, Dispatcher
import callbacks_handler
import commands_handler
import database_manager
import message_handler
import asyncio
import logging
import sys

BOT_TOKEN = "TELEGRAM_TOKEN"
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()
database = database_manager.Database()

commands_handler.init_bot_commands(bot, dp, database)  # Инициализируем обработчики команд
callbacks_handler.init_bot_callbacks(bot, dp, database)  # Инициализируем обработчики callbacks
message_handler.init_bot_message_handler(bot, dp, database)  # Инициализируем обработчики сообщений

async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
