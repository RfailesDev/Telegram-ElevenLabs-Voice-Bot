import os

import database_manager
import messages
import hashlib

database = database_manager.Database()

async def check_user_login(bot, message):
    user_exists = database.check_user_exists(message.from_user.id)
    print(f"user {message.from_user.id} - user_exists = {user_exists}")
    if not user_exists:
        await bot.send_message(message.chat.id, messages.messages["need_register"])
        return False
    return True

async def get_user_audio_folder(user_id):
    filepath = f"users_audio/{user_id}"
    # Создаем папку, если ее не существует
    os.makedirs(filepath, exist_ok=True)
    return filepath

async def hash_string(text, encoding='utf-8'):
    encoded_string = text.encode(encoding)
    sha256_hash = hashlib.sha256(encoded_string)
    return sha256_hash.hexdigest()

async def fix_audios_array_and_delete_messages__(uploaded_audios, bot, userid):
    # Нормализуем данные, чтобы в них не было данных о id сообщений этих самых аудио
    if uploaded_audios:
        print(f"uploaded_audios ======= {uploaded_audios}")
        audios = []
        audios_messages = []
        for audio in uploaded_audios:
            if isinstance(audio, list):
                audios.append(audio[0])
                audios_messages.append(audio[1])
                audios_messages.append(audio[2])
            else:
                audios.append(audio)

        print(f"audios_messages == {audios_messages}")
        await bot.delete_messages(chat_id=userid, message_ids=audios_messages)
        return audios
    else:
        return []

async def fix_audios_array_and_delete_messages(bot, userid):
    # Нормализуем данные, чтобы в них не было данных о id сообщений этих самых аудио
    uploaded_audios = database.get_creating_voice_data(userid)
    fixed_audios = await fix_audios_array_and_delete_messages__(uploaded_audios, bot, userid)
    database.set_creating_voice_data(userid, fixed_audios)