# Обработчик callback-ов
import asyncio
import time

import aiogram
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Filter

import utils
from messages import messages
from aiogram import F

import keyboard_manager as km
import elevenlabs_helper


class TTSVoiceFilter(Filter):
    async def __call__(self, call: CallbackQuery) -> bool:
        return call.data.startswith('tts_select_voice_')

class DeleteVoiceFilter(Filter):
    async def __call__(self, call: CallbackQuery) -> bool:
        return call.data.startswith('remove_select_voice_')


ElevenLabsHelper = elevenlabs_helper.ElevenLabsHelper()


def init_bot_callbacks(bot, dp, database):
    # Открыть меню
    @dp.callback_query(F.data == 'menu')
    async def menu(call: CallbackQuery) -> None:
        database.set_bot_waiting_for(call.from_user.id, "")
        database.set_voice_to_delete(call.from_user.id, "")
        print(f"start!")
        # Нормализуем данные отправленных аудио, чтобы в них не было данных о id сообщений этих самых аудио
        await utils.fix_audios_array_and_delete_messages(bot, call.from_user.id)
        database.register_user(call.from_user.id)
        try:
            await bot.edit_message_text(messages["start_message"], chat_id=call.from_user.id,
                                        message_id=call.message.message_id, reply_markup=km.get_main_keyboard())
        except aiogram.exceptions.TelegramBadRequest:
            await bot.send_message(call.from_user.id, messages["start_message"], reply_markup=km.get_main_keyboard())
        await call.answer()

    # Показать голоса
    @dp.callback_query(F.data == 'voices')
    async def get_voices(call: CallbackQuery) -> None:
        voices = database.get_user_voices(call.from_user.id)
        if voices:
            print(f"voices = {voices}")
            reply_message = f"""
Полный список всех ваших голосов:
            """
            for voice in voices:
                reply_message += f"\n- <strong>{voice["voice_name"]}</strong>"

            reply_message += f"""

<i>Вы можете использовать и выбрать их в синтезе речи!</i>
            """

            keyboard = km.gen_keyboard([
                ["menu", "new_voice", "delete_voice"]
            ])
            await bot.edit_message_text(text=reply_message, chat_id=call.from_user.id,
                                        message_id=call.message.message_id, reply_markup=keyboard)
        else:
            keyboard = km.gen_keyboard([
                ["menu", "new_voice"]
            ])
            await bot.edit_message_text(text=messages["err_no_voices"], chat_id=call.from_user.id,
                                        message_id=call.message.message_id, reply_markup=keyboard)

        await call.answer()

    # Новый голос
    @dp.callback_query(F.data == 'new_voice')
    async def new_voice(call: CallbackQuery) -> None:
        keyboard = km.gen_keyboard([
            ["cancel", "new_voice_next__name"]
        ])
        database.set_bot_waiting_for(call.from_user.id, "get_audio")
        await bot.edit_message_text(text=messages["new_voice1"], chat_id=call.from_user.id, message_id=call.message.message_id, reply_markup=keyboard)
        # await call.message.answer(messages["new_voice1"], reply_markup=keyboard)
        await call.answer()

    # Новый голос
    @dp.callback_query(F.data == 'delete_voice')
    async def delete_voice(call: CallbackQuery) -> None:
        voices = database.get_user_voices(call.from_user.id)
        if voices:
            keyboard_array = []
            for i, voice in enumerate(voices):
                voice_name = voice["voice_name"]
                keyboard_array.append([InlineKeyboardButton(text=voice_name, callback_data=f"remove_select_voice_{i}")])

            keyboard_array.append([InlineKeyboardButton(text="Отменить", callback_data=f"cancel"),
                                   InlineKeyboardButton(text="123321", callback_data=f"new_voice")])
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=keyboard_array
            )
            # await bot.send_message(call.from_user.id, messages["tts"], reply_markup=keyboard)
            try:
                await bot.edit_message_text(text=messages["delete_voice"], chat_id=call.from_user.id,
                                            message_id=call.message.message_id, reply_markup=keyboard)
            except aiogram.exceptions.TelegramBadRequest:
                await bot.send_message(call.from_user.id, messages["delete_voice"], reply_markup=keyboard)
        await call.answer()


    # Новый голос -> 2
    @dp.callback_query(F.data == 'new_voice_next__name')
    async def new_voice_next1(call: CallbackQuery) -> None:
        userid = call.from_user.id
        if database.get_creating_voice_data(userid):
            database.set_bot_waiting_for(call.from_user.id, "get_voice_name")
            keyboard = km.gen_keyboard([
                ["cancel"]
            ])

            # Нормализуем данные отправленных аудио, чтобы в них не было данных о id сообщений этих самых аудио
            await utils.fix_audios_array_and_delete_messages(bot, userid)


            await bot.edit_message_text(text=messages["new_voice2"], chat_id=call.from_user.id,
                                        message_id=call.message.message_id, reply_markup=keyboard)
            # await call.message.answer(messages["new_voice2"], reply_markup=keyboard)
        else:
            message = await bot.send_message(chat_id=call.from_user.id, text=messages["need_voice_files"])
            await asyncio.sleep(1.5)
            await bot.delete_message(call.from_user.id, message.message_id)
        await call.answer()

    # Новый голос -> 3 (Создать новый голос)
    @dp.callback_query(F.data == 'create_new_voice')
    async def create_new_voice(call: CallbackQuery) -> None:
        userid = call.from_user.id
        uploaded_audios = database.get_creating_voice_data(userid)
        database.set_creating_voice_data(userid, [])
        print(f"create uploaded_audios = {uploaded_audios}")

        audios = uploaded_audios[:-1]
        voice_name = uploaded_audios[-1]

        voice = ElevenLabsHelper.clone_voice(name=voice_name, files=audios)
        bot_voice_data = {
            "voice_name": voice_name,
            "voice_audios": audios,
            "voice_id": voice.voice_id
        }
        database.add_user_voice(userid, bot_voice_data)

        await bot.edit_message_text(text=messages["new_voice_done"], chat_id=call.from_user.id,
                                    message_id=call.message.message_id, reply_markup=km.get_main_keyboard())
        # await bot.send_message(userid, messages["new_voice_done"], reply_markup=km.get_main_keyboard())
        await call.answer()

    # Отмена действия
    @dp.callback_query(F.data == 'cancel')
    async def cancel_btn(call: CallbackQuery) -> None:
        userid = call.from_user.id
        database.set_bot_waiting_for(userid, "")
        database.set_voice_to_delete(userid, "")
        # Нормализуем данные отправленных аудио, чтобы в них не было данных о id сообщений этих самых аудио
        await utils.fix_audios_array_and_delete_messages(bot, userid)
        database.set_creating_voice_data(userid, [])
        try:
            await bot.edit_message_text(messages["start_message"], chat_id=call.from_user.id, message_id=call.message.message_id, reply_markup=km.get_main_keyboard())
        except aiogram.exceptions.TelegramBadRequest:
            await bot.send_message(call.from_user.id, messages["start_message"], reply_markup=km.get_main_keyboard())
        await call.answer()

    # Синтез речи
    @dp.callback_query(F.data == 'tts')
    async def tts(call: CallbackQuery) -> None:
        voices = database.get_user_voices(call.from_user.id)
        if voices:
            keyboard_array = []
            for i, voice in enumerate(voices):
                voice_name = voice["voice_name"]
                keyboard_array.append([InlineKeyboardButton(text=voice_name, callback_data=f"tts_select_voice_{i}")])

            keyboard_array.append([InlineKeyboardButton(text="Отменить", callback_data=f"cancel"), InlineKeyboardButton(text="Создать голос", callback_data=f"new_voice")])
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=keyboard_array
            )
            # await bot.send_message(call.from_user.id, messages["tts"], reply_markup=keyboard)
            try:
                await bot.edit_message_text(text=messages["tts"], chat_id=call.from_user.id,
                                            message_id=call.message.message_id, reply_markup=keyboard)
            except aiogram.exceptions.TelegramBadRequest:
                await bot.send_message(call.from_user.id, messages["tts"], reply_markup=keyboard)
        await call.answer()

    # Выбор голоса
    @dp.callback_query(TTSVoiceFilter())
    async def select_voice(call: CallbackQuery) -> None:
        cancel_keyboard = km.gen_keyboard([
            ["cancel"]
        ])
        try:
            voice_index = int(call.data.split('_')[-1])
            voices = database.get_user_voices(call.from_user.id)

            if 0 <= voice_index < len(voices):
                selected_voice = voices[voice_index]
                # Здесь используйте selected_voice для дальнейшей работы, например:
                # await call.message.answer(f"Вы выбрали голос: {selected_voice['voice_name']}")
                # await call.message.answer(messages["tts_enter_text"], reply_markup=cancel_keyboard)
                reply_text = f"Вы выбрали голос: {selected_voice['voice_name']}\n{messages["tts"]}"
                await bot.edit_message_text(text=reply_text, chat_id=call.from_user.id,
                                            message_id=call.message.message_id, reply_markup=cancel_keyboard)
                database.set_selected_voice(call.from_user.id, voice_index)
                database.set_bot_waiting_for(call.from_user.id, f"")

            else:
                await call.message.answer("Выбран неверный голос.")

        except (ValueError, IndexError):
            await call.message.answer("Ошибка при обработке запроса.")

        await call.answer()

    # Удаление голоса
    @dp.callback_query(DeleteVoiceFilter())
    async def delete_voice_callback(call: CallbackQuery) -> None:
        keyboard = km.gen_keyboard([
            ["cancel", "ok"]
        ])
        try:
            voice_index = int(call.data.split('_')[-1])
            print(f"||| voice_index = {voice_index}")
            voices = database.get_user_voices(call.from_user.id)

            if 0 <= voice_index < len(voices):
                selected_voice = voices[voice_index]
                # Здесь используйте selected_voice для дальнейшей работы, например:
                # await call.message.answer(f"Вы выбрали голос: {selected_voice['voice_name']}")
                # await call.message.answer(messages["tts_enter_text"], reply_markup=cancel_keyboard)

                reply_text = f"""
<strong>• Удаление голоса</strong>

Вы хотите удалить этот голос?
(<strong>{selected_voice['voice_name']}</strong>)
                """
                await bot.edit_message_text(text=reply_text, chat_id=call.from_user.id,
                                            message_id=call.message.message_id, reply_markup=keyboard)
                database.set_voice_to_delete(call.from_user.id, voice_index)
                database.set_bot_waiting_for(call.from_user.id, f"delete_voice_check")

            else:
                await call.message.answer("Выбран неверный голос.")

        except (ValueError, IndexError):
            await call.message.answer("Ошибка при обработке запроса.")

        await call.answer()

    # Подтверждение
    @dp.callback_query(F.data == 'ok')
    async def ok(call: CallbackQuery) -> None:
        if database.get_bot_waiting_for(call.from_user.id) == "delete_voice_check":
            voices = database.get_user_voices(call.from_user.id)
            voice_to_delete = database.get_voice_to_delete(call.from_user.id)
            print(f"voice_to_delete ====+++ = {voice_to_delete}")
            print(f"++++ voices = {voices}")
            print(f"++++ vvv2222 = {0 <= voice_to_delete < len(voices)}")
            if voices and voice_to_delete!="" and 0 <= voice_to_delete < len(voices):
                selected_voice = voices[voice_to_delete]
                eleven_voice_id = selected_voice["voice_id"]  # Id голоса в ElevenLabs
                database.remove_user_voice(call.from_user.id, voice_to_delete)  # Удаляем голос в боте
                try:
                    ElevenLabsHelper.delete_voice(eleven_voice_id)  # Удаляем голос в elevenlabs
                except Exception as e:
                    print(f"Elevenlabs error when delete voice: {e}")
                # await bot.send_message(call.from_user.id, messages["tts"], reply_markup=keyboard)
                database.set_voice_to_delete(call.from_user.id, "")
                message = await bot.send_message(call.from_user.id, f"Голос <strong>{selected_voice["voice_name"]}</strong> успешно удален!")
                await asyncio.sleep(1.5)
                await bot.delete_message(call.from_user.id, message.message_id)
                await get_voices(call)  # Показываем список голосов
            await call.answer()

