import psycopg2
from config import load_config

def get_connection():
    try:
        return psycopg2.connect(**load_config())
    except Exception as error:
        print(f"Ошибка подключения: {error}")
        return None

def search_pattern(pattern):
    """Вызывает функцию поиска по паттерну."""
    conn = get_connection()
    if not conn: return
    try:
        with conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM get_contacts_by_pattern(%s)", (pattern,))
            results = cur.fetchall()
            print("\nРезультаты поиска:")
            for row in results:
                print(f"- {row[0]}: {row[1]}")
            if not results: print("Ничего не найдено.")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        conn.close()

def upsert_user(name, phone):
    """Вызывает процедуру добавления/обновления пользователя."""
    conn = get_connection()
    if not conn: return
    try:
        with conn, conn.cursor() as cur:
            cur.execute("CALL upsert_contact(%s, %s)", (name, phone))
        print(f"Контакт '{name}' успешно добавлен/обновлен.")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        conn.close()

def bulk_insert(names, phones):
    """Вызывает процедуру массовой вставки с валидацией."""
    conn = get_connection()
    if not conn: return
    try:
        with conn, conn.cursor() as cur:
            # Передаем списки и пустой список для INOUT параметра invalid_data
            cur.execute("CALL bulk_insert_contacts(%s, %s, %s)", (names, phones, []))
            invalid_data = cur.fetchone()[0]
            
            print("Массовая вставка завершена.")
            if invalid_data:
                print("Эти контакты не были добавлены (неверный формат телефона):")
                for bad_record in invalid_data:
                    print(f"- {bad_record}")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        conn.close()

def paginated_query(limit, offset):
    """Вызывает функцию постраничного вывода."""
    conn = get_connection()
    if not conn: return
    try:
        with conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM get_contacts_paginated(%s, %s)", (limit, offset))
            results = cur.fetchall()
            print(f"\nКонтакты (Limit: {limit}, Offset: {offset}):")
            for row in results:
                print(f"- {row[0]}: {row[1]}")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        conn.close()

def delete_user(search_val):
    """Вызывает процедуру удаления."""
    conn = get_connection()
    if not conn: return
    try:
        with conn, conn.cursor() as cur:
            cur.execute("CALL delete_contact(%s)", (search_val,))
        print(f"Команда удаления выполнена для: {search_val}")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        conn.close()

def main():
    while True:
        print("\n--- ТЕЛЕФОННАЯ КНИГА (Stored Procedures) ---")
        print("1. Поиск контакта (по паттерну)")
        print("2. Добавить/Обновить контакт (Upsert)")
        print("3. Массовая вставка с проверкой (Bulk Insert)")
        print("4. Постраничный вывод (Pagination)")
        print("5. Удалить контакт")
        print("6. Выход")
        
        choice = input("Выберите действие (1-6): ")
        
        if choice == '1':
            pattern = input("Введите часть имени или номера: ")
            search_pattern(pattern)
        elif choice == '2':
            name = input("Введите имя: ")
            phone = input("Введите телефон: ")
            upsert_user(name, phone)
        elif choice == '3':
            print("Введите данные через запятую (например: Иван,Анна / +7111,+7222)")
            names = input("Имена: ").split(',')
            phones = input("Телефоны (введи один с буквами для теста ошибки): ").split(',')
            if len(names) == len(phones):
                bulk_insert([n.strip() for n in names], [p.strip() for p in phones])
            else:
                print("Ошибка: Количество имен и телефонов не совпадает!")
        elif choice == '4':
            limit = int(input("Сколько записей вывести (Limit)? ") or 5)
            offset = int(input("Сколько записей пропустить (Offset)? ") or 0)
            paginated_query(limit, offset)
        elif choice == '5':
            search_val = input("Введите имя или номер для удаления: ")
            delete_user(search_val)
        elif choice == '6':
            print("До свидания!")
            break
        else:
            print("Неверный ввод.")

if __name__ == '__main__':
    main()