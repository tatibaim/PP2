# Этот же скрипт отвечает за подключение к бд и первоначальную настройку - создание таблицы contacts.
import psycopg2
from config import load_config

def create_table():
    #Создает таблицу для телефонной книги, если она еще не существует
    command = """
    CREATE TABLE IF NOT EXISTS contacts (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        phone VARCHAR(50) NOT NULL UNIQUE
    )
    """
    conn = None
    try:
        params = load_config()
        print("Подключение к PostgreSQL...")
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        
        cur.execute(command)
        cur.close()
        conn.commit()
        print("Таблица 'contacts' успешно создана или уже существует.")
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Ошибка БД: {error}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    create_table()