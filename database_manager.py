import sqlite3
import json


class Database:
    def __init__(self, db_name="users.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                parameters TEXT,
                subscription TEXT,
                used_tokens INTEGER,
                voices TEXT,
                selected_voice TEXT,
                waiting_for TEXT,
                creating_voice_data TEXT,
                voice_to_delete TEXT
            )
        ''')
        self.conn.commit()

    def register_user(self, user_id):
        try:
            self.cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
            if self.cursor.fetchone():
                return False

            default_data = json.dumps({})
            default_data2 = json.dumps([])
            self.cursor.execute('''
                            INSERT INTO users (id, parameters, subscription, used_tokens, voices, selected_voice, waiting_for, creating_voice_data, voice_to_delete)
                            VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?)
                        ''', (
                user_id, default_data, default_data, default_data2, "", "", default_data2,
                ""))  # creating_voice_data по умолчанию NULL
            self.conn.commit()
            return True

        except Exception as e:
            print(f"Ошибка при регистрации пользователя: {e}")
            return False

    def get_user_data(self, user_id):
        try:
            self.cursor.execute("SELECT parameters, subscription, used_tokens, voices FROM users WHERE id = ?",
                                (user_id,))
            result = self.cursor.fetchone()
            if result:
                parameters, subscription, used_tokens, voices = result
                return {
                    "parameters": json.loads(parameters),
                    "subscription": json.loads(subscription),
                    "used_tokens": used_tokens,
                    "voices": json.loads(voices)
                }
            else:
                return None
        except Exception as e:
            print(f"Ошибка при получении данных пользователя: {e}")
            return None

    def check_user_exists(self, user_id):
        try:
            self.cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
            return self.cursor.fetchone() is not None
        except Exception as e:
            print(f"Ошибка при проверке существования пользователя: {e}")
            return False

    def set_user_parameters(self, user_id, parameters):
        try:
            parameters_json = json.dumps(parameters)
            self.cursor.execute("UPDATE users SET parameters = ? WHERE id = ?", (parameters_json, user_id))
            self.conn.commit()
            return True

        except Exception as e:
            print(f"Ошибка при установке параметров пользователя: {e}")
            return False

    def set_user_subscription(self, user_id, subscription):
        try:
            subscription_json = json.dumps(subscription)
            self.cursor.execute("UPDATE users SET subscription = ? WHERE id = ?", (subscription_json, user_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка при установке подписки пользователя: {e}")
            return False

    def update_used_tokens(self, user_id, tokens_used):
        try:
            self.cursor.execute("UPDATE users SET used_tokens = used_tokens + ? WHERE id = ?", (tokens_used, user_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка при обновлении использованных токенов: {e}")
            return False

    def get_user_voices(self, user_id):
        user_data = self.get_user_data(user_id)
        return user_data.get("voices", []) if user_data else None

    def add_user_voice(self, user_id, voice_data):
        voices = self.get_user_voices(user_id) or []
        #  Здесь нужно определить логику добавления voice_data.
        #  Например, если voice_data это словарь с именем голоса как ключ:
        voices.append(voice_data)  # или voices[new_voice_name] = voice_data
        return self.set_user_voices(user_id, voices)

    def remove_user_voice(self, user_id, voice_id):
        print(f"[][][][][][][] remove_user_voice = {user_id}, {voice_id}")
        voices = self.get_user_voices(user_id) or []
        if 0 <= voice_id < len(voices):
            del voices[voice_id]
            print(f"UPDATED VOICES: {voices}")
            return self.set_user_voices(user_id, voices)
        return False  # voice not found

    def set_user_voices(self, user_id, voices):
        try:
            voices_json = json.dumps(voices)
            self.cursor.execute("UPDATE users SET voices = ? WHERE id = ?", (voices_json, user_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка при установке голосов пользователя: {e}")
            return False

    def set_bot_waiting_for(self, user_id, waiting_for_value):
        print(f"set_bot_waiting_for = {user_id}, waiting_for_value = {waiting_for_value}")
        try:
            self.cursor.execute("UPDATE users SET waiting_for = ? WHERE id = ?", (waiting_for_value, user_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка при установке waiting_for: {e}")
            return False

    def get_bot_waiting_for(self, user_id):
        try:
            self.cursor.execute("SELECT waiting_for FROM users WHERE id = ?", (user_id,))
            result = self.cursor.fetchone()
            return result[
                0] if result else None  # Возвращаем значение waiting_for или None, если пользователь не найден
        except Exception as e:
            print(f"Ошибка при получении waiting_for: {e}")
            return None

    def set_creating_voice_data(self, user_id, data):
        print(f"||set_creating_voice_data = {data}")
        try:
            data_json = json.dumps(data)
            self.cursor.execute("UPDATE users SET creating_voice_data = ? WHERE id = ?", (data_json, user_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка при установке creating_voice_data: {e}")
            return False

    def get_creating_voice_data(self, user_id):
        try:
            self.cursor.execute("SELECT creating_voice_data FROM users WHERE id = ?", (user_id,))
            result = self.cursor.fetchone()
            if result and result[0]:
                if result[0] == "":  # Проверяем на пустую строку
                    return []  # или {} -  в зависимости от того, что вам нужно по умолчанию
                else:
                    return json.loads(result[0])
            else:
                return []  # Возвращаем пустой список, если данных нет или они NULL
        except json.JSONDecodeError as e:
            print(f"Ошибка декодирования JSON в creating_voice_data: {e}")
            return []  # Возвращаем пустой список в случае ошибки JSON
        except Exception as e:
            print(f"Ошибка при получении creating_voice_data: {e}")
            return []  # Возвращаем пустой список в случае других ошибок

    def set_selected_voice(self, user_id, voice_id):
        try:
            self.cursor.execute("UPDATE users SET selected_voice = ? WHERE id = ?", (str(voice_id), user_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка при установке set_selected_voice: {e}")
            return False

    def get_selected_voice(self, user_id):
        try:
            self.cursor.execute("SELECT selected_voice FROM users WHERE id = ?", (user_id,))
            result = self.cursor.fetchone()
            if result and result[0]:
                return int(result[0])
            else:
                return ""  # Возвращаем пустой список, если данных нет или они NULL
        except Exception as e:
            print(f"Ошибка при получении get_selected_voice: {e}")
            return []  # Возвращаем пустой список в случае других ошибок

    def set_voice_to_delete(self, user_id, voice_id):
        try:
            self.cursor.execute("UPDATE users SET voice_to_delete = ? WHERE id = ?", (str(voice_id), user_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка при установке set_delete_voice: {e}")
            return False

    def get_voice_to_delete(self, user_id):
        try:
            self.cursor.execute("SELECT voice_to_delete FROM users WHERE id = ?", (user_id,))
            result = self.cursor.fetchone()
            if result and result[0]:
                return int(result[0])
            else:
                return ""  # Возвращаем пустой список, если данных нет или они NULL
        except Exception as e:
            print(f"Ошибка при получении set_delete_voice: {e}")
            return []  # Возвращаем пустой список в случае других ошибок

    def close_connection(self):
        self.conn.close()
