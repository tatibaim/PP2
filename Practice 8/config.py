def load_config():
    # Возвращает параметры подключения к PostgreSQL
    return {
        "host": "localhost",
        "database": "phonebook_db", # имя моей бд
        "user": "postgres",         # мой пользователь бд
        "password": "12345678" # мой пароль
    }

# Этот файл будет хранить настройки для подключения к базе данных