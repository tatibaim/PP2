import psycopg2
import csv
from config import load_config

def get_connection():
    #Устанавливает и возвращает подключение к бд
    try:
        return psycopg2.connect(**load_config())
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Ошибка подключения: {error}")
        return None

def import_from_csv(filename):
    #Импортирует контакты из CSV файла
    conn = get_connection()
    if not conn: return

    try:
        with conn, conn.cursor() as cur:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Пропускаем заголовок (name, phone)
                for row in reader:
                    if len(row) == 2:
                        name, phone = row[0].strip(), row[1].strip()
                        # Используем ON CONFLICT DO NOTHING, чтобы избежать ошибок дубликатов
                        cur.execute(
                            "INSERT INTO contacts (name, phone) VALUES (%s, %s) ON CONFLICT (phone) DO NOTHING",
                            (name, phone)
                        )
        print("Данные из CSV успешно импортированы.")
    except Exception as e:
        print(f"Ошибка при импорте CSV: {e}")
    finally:
        conn.close()

def add_contact(name, phone):
    #Добавляет один контакт через консоль
    conn = get_connection()
    if not conn: return
    try:
        with conn, conn.cursor() as cur:
            cur.execute("INSERT INTO contacts (name, phone) VALUES (%s, %s)", (name, phone))
        print(f"Контакт '{name}' успешно добавлен.")
    except psycopg2.errors.UniqueViolation:
        print(f"Ошибка: Номер {phone} уже существует в базе.")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        conn.close()

def update_contact(search_val, new_name=None, new_phone=None):
    """Обновляет имя или телефон контакта."""
    conn = get_connection()
    if not conn: return
    try:
        with conn, conn.cursor() as cur:
            if new_name and new_phone:
                # Обновляем сразу и имя, и телефон за один проход
                cur.execute("UPDATE contacts SET name = %s, phone = %s WHERE name = %s OR phone = %s", (new_name, new_phone, search_val, search_val))
            elif new_name:
                cur.execute("UPDATE contacts SET name = %s WHERE name = %s OR phone = %s", (new_name, search_val, search_val))
            elif new_phone:
                cur.execute("UPDATE contacts SET phone = %s WHERE name = %s OR phone = %s", (new_phone, search_val, search_val))
            
            if cur.rowcount > 0:
                print(f"Контакт обновлен. Изменено строк: {cur.rowcount}")
            else:
                print("Контакт не найден.")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        conn.close()

def query_contacts(filter_type, filter_val):
    #Ищет контакты по имени (точное совпадение) или префиксу телефона.
    conn = get_connection()
    if not conn: return
    try:
        with conn, conn.cursor() as cur:
            if filter_type == '1': # По имени
                cur.execute("SELECT name, phone FROM contacts WHERE name ILIKE %s", (f"%{filter_val}%",))
            elif filter_type == '2': # По префиксу телефона
                cur.execute("SELECT name, phone FROM contacts WHERE phone LIKE %s", (f"{filter_val}%",))
            
            results = cur.fetchall()
            if results:
                print("\nНайденные контакты:")
                for row in results:
                    print(f"- Имя: {row[0]}, Телефон: {row[1]}")
            else:
                print("Контакты не найдены.")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        conn.close()

def delete_contact(search_val):
    #Удаляет контакт по имени или номеру телефона
    conn = get_connection()
    if not conn: return
    try:
        with conn, conn.cursor() as cur:
            cur.execute("DELETE FROM contacts WHERE name = %s OR phone = %s", (search_val, search_val))
            if cur.rowcount > 0:
                print(f"Контакт удален. Удалено строк: {cur.rowcount}")
            else:
                print("Контакт для удаления не найден.")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        conn.close()

def main():
    while True:
        print("\n--- ТЕЛЕФОННАЯ КНИГА ---")
        print("1. Импорт контактов из CSV")
        print("2. Добавить контакт вручную")
        print("3. Обновить контакт")
        print("4. Найти контакт")
        print("5. Удалить контакт")
        print("6. Выход")
        
        choice = input("Выберите действие (1-6): ")
        
        if choice == '1':
            import_from_csv('contacts.csv')
        elif choice == '2':
            name = input("Введите имя: ")
            phone = input("Введите телефон: ")
            add_contact(name, phone)
        elif choice == '3':
            search_val = input("Введите текущее имя ИЛИ телефон контакта, который нужно обновить: ")
            new_name = input("Введите новое имя (нажмите Enter, чтобы пропустить): ")
            new_phone = input("Введите новый телефон (нажмите Enter, чтобы пропустить): ")
            update_contact(search_val, new_name if new_name else None, new_phone if new_phone else None)
        elif choice == '4':
            print("Фильтры: 1 - По имени, 2 - По префиксу телефона")
            f_type = input("Выберите фильтр (1 или 2): ")
            f_val = input("Введите значение для поиска: ")
            query_contacts(f_type, f_val)
        elif choice == '5':
            search_val = input("Введите точное имя ИЛИ телефон для удаления: ")
            delete_contact(search_val)
        elif choice == '6':
            print("Выход из программы. До свидания!")
            break
        else:
            print("Неверный ввод. Попробуйте снова.")

if __name__ == '__main__':
    main()