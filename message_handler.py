# Обработчик сообщений

from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import BufferedInputFile
from messages import messages
from aiogram import F

import keyboard_manager as km
import elevenlabs_helper
import utils

ElevenLabsHelper = elevenlabs_helper.ElevenLabsHelper()


async def new_voice_final(userid, voice_name, database, bot):
    database.set_bot_waiting_for(userid, "")

    uploaded_audios = database.get_creating_voice_data(userid)
    reply_message = f"""
Это название будет использоваться для нового голоса!

Вы загрузили {len(uploaded_audios)} файлов с аудио, они будут использованы для клонирования!

Создать голос?
    """
    add_voice = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отменить", callback_data="cancel"),
             InlineKeyboardButton(text="Создать голос", callback_data="create_new_voice")],
        ]
    )
    print(f"___ uploaded_audios = {uploaded_audios}")
    uploaded_audios.append(voice_name)
    database.set_creating_voice_data(userid, uploaded_audios)

    await bot.send_message(userid, reply_message, reply_markup=add_voice)


async def process_input_audio(message, user_id, message_media, database, bot):
    print("AUDIO!!!!!")
    if database.get_bot_waiting_for(user_id) == "get_audio":
        reply_message = await message.reply("↻ Скачиваю")
        filename = f"{message_media.file_id}_{user_id}.mp3"
        filepath = await utils.get_user_audio_folder(user_id)

        await bot.download(message_media.file_id, f"{filepath}/{filename}")

        await bot.edit_message_text(text="✔ Готово", chat_id=user_id,
                                    message_id=reply_message.message_id)

        # Добавляем аудио-файл в список добавленных
        voice_creating_data = database.get_creating_voice_data(user_id)
        print(f"voice_creating_data == {voice_creating_data}")
        voice_creating_data.append([f"{filepath}/{filename}", message.message_id, reply_message.message_id])
        database.set_creating_voice_data(user_id, voice_creating_data)
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Создать голос", callback_data="new_voice")],
            ]
        )
        await message.reply(text=messages["err_audio_not_req"], reply_markup=keyboard)


def init_bot_message_handler(bot, dp, database):
    @dp.message(F.document)
    async def get_document(message: Message) -> None:
        # Пользователь отправляет файл
        if message.document.file_name.endswith(".wav"):
            await process_input_audio(message, message.from_user.id, message_media=message.document, database=database,
                                      bot=bot)
        elif message.document.file_name.endswith(".ogg"):
            await process_input_audio(message, message.from_user.id, message_media=message.document, database=database,
                                      bot=bot)

    @dp.message(F.audio)
    async def get_audio(message: Message) -> None:
        # Пользователь отправляет аудио
        await process_input_audio(message, message.from_user.id, message_media=message.audio, database=database,
                                  bot=bot)

    @dp.message(F.sticker)
    async def get_audio(message: Message) -> None:
        print(f"sticker = {message.sticker}")

    @dp.message(F.voice)
    async def get_audio(message: Message) -> None:
        # Пользователь отправляет аудио
        await process_input_audio(message, message.from_user.id, message_media=message.voice, database=database,
                                  bot=bot)

    @dp.message()
    async def user_message(message: Message) -> None:
        # Пользователь отправляет простое сообщение
        if await utils.check_user_login(bot, message):
            bot_waiting_for = database.get_bot_waiting_for(message.from_user.id)

            match bot_waiting_for:
                case "get_voice_name":
                    # Если бот ожидает ввод названия нового голоса, то включаем следующий этап.
                    await new_voice_final(message.from_user.id, message.text, database=database, bot=bot)
                case "":
                    # Если бот ничего не ожидает, значит нужно это синтезировать
                    voices = database.get_user_voices(message.from_user.id)
                    voice_index = database.get_selected_voice(user_id=message.from_user.id)
                    selected_voice = voices[voice_index]
                    tts_text = message.text

                    # Проверка на выбранный голос
                    if not selected_voice:
                        keyboard = InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(text="Главное меню", callback_data="menu"),
                                 InlineKeyboardButton(text="Озвучить текст", callback_data="tts")]
                            ]
                        )
                        await message.answer(messages["tts_empty_voice"], reply_markup=keyboard)
                        return

                    # Проверка на введенный текст для синтеза
                    if not tts_text:
                        await message.answer(messages["tts_empty_text"])
                        return

                    audio = ElevenLabsHelper.tts(text=tts_text, voice=selected_voice["voice_id"])

                    hash_name = await utils.hash_string(tts_text)
                    filename = f"tts_{hash_name}_{message.from_user.id}.mp3"
                    filepath = await utils.get_user_audio_folder(message.from_user.id)
                    path = f"{filepath}/{filename}"
                    ElevenLabsHelper.save_audio(audio, path)

                    keyboard = km.gen_keyboard([
                        ["menu", "tts"]
                    ])

                    database.set_bot_waiting_for(message.from_user.id, "")

                    await bot.send_voice(message.from_user.id, voice=BufferedInputFile.from_file(path=path),
                                         caption=f"<strong>VadimAI</strong>, голос: {selected_voice['voice_name']}",
                                         reply_markup=keyboard)
