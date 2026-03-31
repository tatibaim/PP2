import psycopg2
from config import load_config
import os

def setup_database():
    # Создает таблицу и загружает функции/процедуры из SQL файлов
    create_table_command = """
    CREATE TABLE IF NOT EXISTS contacts (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        phone VARCHAR(50) NOT NULL UNIQUE
    )
    """
    conn = None
    try:
        conn = psycopg2.connect(**load_config())
        cur = conn.cursor()
        
        # Создаем таблицу
        cur.execute(create_table_command)
        
        # Читаем и выполняем функции
        if os.path.exists('functions.sql'):
            with open('functions.sql', 'r', encoding='utf-8') as f:
                cur.execute(f.read())
                
        # Читаем и выполняем процедуры
        if os.path.exists('procedures.sql'):
            with open('procedures.sql', 'r', encoding='utf-8') as f:
                cur.execute(f.read())
                
        conn.commit()
        print("База данных, функции и процедуры успешно инициализированы!")
        
    except Exception as error:
        print(f"Ошибка БД: {error}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    setup_database()