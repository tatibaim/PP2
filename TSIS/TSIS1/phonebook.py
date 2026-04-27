import csv
import json
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2 import errors

from config import load_config
from connect import setup_database


BASE_DIR = Path(__file__).resolve().parent
VALID_PHONE_TYPES = {"home", "work", "mobile"}
SORT_OPTIONS = {
    "1": ("name", "c.name ASC"),
    "2": ("birthday", "c.birthday ASC NULLS LAST, c.name ASC"),
    "3": ("date added", "c.created_at DESC, c.name ASC"),
}


def get_connection():
    try:
        return psycopg2.connect(**load_config())
    except Exception as error:
        print(f"Connection error: {error}")
        return None


def resolve_path(filename):
    path = Path(filename)
    if path.is_absolute():
        return path
    return BASE_DIR / path


def parse_birthday(raw_value):
    if raw_value in (None, ""):
        return None
    if hasattr(raw_value, "isoformat") and not isinstance(raw_value, str):
        return raw_value

    try:
        return datetime.strptime(str(raw_value).strip(), "%Y-%m-%d").date()
    except ValueError as error:
        raise ValueError("Birthday must use YYYY-MM-DD format.") from error


def normalize_group_name(raw_value):
    value = (raw_value or "Other").strip()
    return value.title() if value else "Other"


def normalize_phone_type(raw_value):
    value = (raw_value or "mobile").strip().lower()
    if value not in VALID_PHONE_TYPES:
        raise ValueError("Phone type must be one of: home, work, mobile.")
    return value


def normalize_phone_list(raw_phones, fallback_phone=None, fallback_type=None):
    phones = []
    seen = set()

    if isinstance(raw_phones, list):
        for item in raw_phones:
            if isinstance(item, dict):
                phone = str(item.get("phone", "")).strip()
                phone_type = normalize_phone_type(item.get("type"))
            else:
                phone = str(item).strip()
                phone_type = normalize_phone_type(fallback_type)

            if phone and phone not in seen:
                phones.append({"phone": phone, "type": phone_type})
                seen.add(phone)

    if fallback_phone:
        phone = str(fallback_phone).strip()
        phone_type = normalize_phone_type(fallback_type)
        if phone and phone not in seen:
            phones.insert(0, {"phone": phone, "type": phone_type})
            seen.add(phone)

    if not phones:
        raise ValueError("At least one phone number is required.")

    return phones


def ensure_group(cur, group_name):
    cur.execute(
        """
        INSERT INTO groups (name)
        VALUES (%s)
        ON CONFLICT (name) DO UPDATE
        SET name = EXCLUDED.name
        RETURNING id
        """,
        (normalize_group_name(group_name),),
    )
    return cur.fetchone()[0]


def find_single_contact_id(cur, name):
    cur.execute(
        """
        SELECT COUNT(*), MIN(id)
        FROM contacts
        WHERE name = %s
        """,
        (name,),
    )
    match_count, contact_id = cur.fetchone()

    if match_count > 1:
        raise ValueError(
            f"More than one contact named '{name}' exists. Resolve duplicates first."
        )

    return contact_id


def phone_belongs_to_other_contact(cur, phone, contact_id=None):
    cur.execute(
        """
        SELECT c.id, c.name
        FROM contacts c
        WHERE c.phone = %s
        LIMIT 1
        """,
        (phone,),
    )
    row = cur.fetchone()
    if row and row[0] != contact_id:
        return row

    cur.execute(
        """
        SELECT c.id, c.name
        FROM phones p
        JOIN contacts c ON c.id = p.contact_id
        WHERE p.phone = %s
        LIMIT 1
        """,
        (phone,),
    )
    row = cur.fetchone()
    if row and row[0] != contact_id:
        return row

    return None


def fetch_groups():
    conn = get_connection()
    if not conn:
        return []

    try:
        with conn, conn.cursor() as cur:
            cur.execute("SELECT name FROM groups ORDER BY name")
            return [row[0] for row in cur.fetchall()]
    except Exception as error:
        print(f"Could not load groups: {error}")
        return []
    finally:
        conn.close()


def query_contact_rows(where_clauses=None, params=None, order_sql=None):
    conn = get_connection()
    if not conn:
        return []

    query = """
        SELECT
            c.id,
            c.name,
            c.email,
            c.birthday,
            c.created_at,
            COALESCE(g.name, 'Other') AS group_name,
            c.phone AS primary_phone,
            p.phone,
            p.type
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        LEFT JOIN phones p ON p.contact_id = c.id
    """

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += f" ORDER BY {order_sql or SORT_OPTIONS['1'][1]}, p.id"

    try:
        with conn, conn.cursor() as cur:
            cur.execute(query, params or [])
            return cur.fetchall()
    except Exception as error:
        print(f"Query error: {error}")
        return []
    finally:
        conn.close()


def rows_to_contacts(rows):
    contacts = {}

    for row in rows:
        contact_id = row[0]
        phone_value = row[7]
        phone_type = row[8]

        if contact_id not in contacts:
            contacts[contact_id] = {
                "id": contact_id,
                "name": row[1],
                "email": row[2],
                "birthday": row[3],
                "created_at": row[4],
                "group": row[5],
                "primary_phone": row[6],
                "phones": [],
            }

        if phone_value and phone_value not in {item["phone"] for item in contacts[contact_id]["phones"]}:
            contacts[contact_id]["phones"].append(
                {"phone": phone_value, "type": phone_type or "mobile"}
            )

    for contact in contacts.values():
        if not contact["phones"] and contact["primary_phone"]:
            contact["phones"].append(
                {"phone": contact["primary_phone"], "type": "mobile"}
            )

    return list(contacts.values())


def print_contacts(contacts):
    if not contacts:
        print("No contacts found.")
        return

    for index, contact in enumerate(contacts, start=1):
        phones_text = ", ".join(
            f"{item['type']}: {item['phone']}" for item in contact["phones"]
        ) or "-"
        birthday = contact["birthday"].isoformat() if contact["birthday"] else "-"
        created_at = (
            contact["created_at"].strftime("%Y-%m-%d %H:%M")
            if contact["created_at"]
            else "-"
        )

        print(f"\n{index}. {contact['name']}")
        print(f"   Group: {contact['group']}")
        print(f"   Email: {contact['email'] or '-'}")
        print(f"   Birthday: {birthday}")
        print(f"   Added: {created_at}")
        print(f"   Phones: {phones_text}")


def choose_sort_sql():
    print("\nSort by:")
    print("1. Name")
    print("2. Birthday")
    print("3. Date added")

    choice = input("Choose sort option (1-3, default 1): ").strip() or "1"
    return SORT_OPTIONS.get(choice, SORT_OPTIONS["1"])[1]


def show_contacts_with_filters():
    groups = fetch_groups()
    if groups:
        print("\nAvailable groups:", ", ".join(groups))

    group_name = input("Group filter (leave blank for all): ").strip()
    email_query = input("Email contains (leave blank for all): ").strip()
    order_sql = choose_sort_sql()

    where_clauses = []
    params = []

    if group_name:
        where_clauses.append("COALESCE(g.name, 'Other') ILIKE %s")
        params.append(group_name)

    if email_query:
        where_clauses.append("COALESCE(c.email, '') ILIKE %s")
        params.append(f"%{email_query}%")

    contacts = rows_to_contacts(query_contact_rows(where_clauses, params, order_sql))
    print_contacts(contacts)


def fetch_all_contacts(order_sql=None):
    return rows_to_contacts(query_contact_rows(order_sql=order_sql or SORT_OPTIONS["1"][1]))


def create_contact(cur, name, email, birthday, group_name, phones):
    group_id = ensure_group(cur, group_name or "Other")
    primary_phone = phones[0]["phone"]

    cur.execute(
        """
        INSERT INTO contacts (name, phone, email, birthday, group_id)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (name, primary_phone, email, birthday, group_id),
    )
    contact_id = cur.fetchone()[0]

    for phone in phones:
        cur.execute(
            """
            INSERT INTO phones (contact_id, phone, type)
            VALUES (%s, %s, %s)
            ON CONFLICT (contact_id, phone) DO UPDATE
            SET type = EXCLUDED.type
            """,
            (contact_id, phone["phone"], phone["type"]),
        )


def replace_contact(cur, contact_id, name, email, birthday, group_name, phones):
    group_id = ensure_group(cur, group_name or "Other")
    primary_phone = phones[0]["phone"]

    cur.execute(
        """
        UPDATE contacts
        SET name = %s,
            phone = %s,
            email = %s,
            birthday = %s,
            group_id = %s
        WHERE id = %s
        """,
        (name, primary_phone, email, birthday, group_id, contact_id),
    )
    cur.execute("DELETE FROM phones WHERE contact_id = %s", (contact_id,))

    for phone in phones:
        cur.execute(
            """
            INSERT INTO phones (contact_id, phone, type)
            VALUES (%s, %s, %s)
            """,
            (contact_id, phone["phone"], phone["type"]),
        )


def import_from_csv(filename):
    csv_path = resolve_path(filename)
    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        return

    conn = get_connection()
    if not conn:
        return

    imported = 0
    skipped = 0

    try:
        with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)

            with conn, conn.cursor() as cur:
                for row in reader:
                    name = (row.get("name") or "").strip()
                    phone = (row.get("phone") or "").strip()
                    if not name or not phone:
                        continue

                    email = (row.get("email") or "").strip() or None
                    birthday = parse_birthday((row.get("birthday") or "").strip())
                    raw_group_name = (row.get("group") or "").strip()
                    group_name = (
                        normalize_group_name(raw_group_name) if raw_group_name else None
                    )
                    phone_type = normalize_phone_type(row.get("phone_type"))

                    contact_id = find_single_contact_id(cur, name)
                    phone_owner = phone_belongs_to_other_contact(cur, phone, contact_id)

                    if phone_owner:
                        print(
                            f"Skipped CSV row for {name}: phone {phone} already belongs to "
                            f"{phone_owner[1]}."
                        )
                        skipped += 1
                        continue

                    if contact_id:
                        group_id = ensure_group(cur, group_name) if group_name else None
                        cur.execute(
                            """
                            UPDATE contacts
                            SET email = COALESCE(%s, email),
                                birthday = COALESCE(%s, birthday),
                                group_id = COALESCE(%s, group_id)
                            WHERE id = %s
                            """,
                            (email, birthday, group_id, contact_id),
                        )
                        cur.execute(
                            """
                            INSERT INTO phones (contact_id, phone, type)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (contact_id, phone) DO UPDATE
                            SET type = EXCLUDED.type
                            """,
                            (contact_id, phone, phone_type),
                        )
                    else:
                        create_contact(
                            cur,
                            name,
                            email,
                            birthday,
                            group_name or "Other",
                            [{"phone": phone, "type": phone_type}],
                        )

                    imported += 1

        print(f"CSV import finished. Imported rows: {imported}, skipped rows: {skipped}")
    except Exception as error:
        print(f"CSV import error: {error}")
    finally:
        conn.close()


def export_to_json(filename):
    json_path = resolve_path(filename)
    contacts = fetch_all_contacts()

    payload = []
    for contact in contacts:
        payload.append(
            {
                "name": contact["name"],
                "email": contact["email"],
                "birthday": (
                    contact["birthday"].isoformat() if contact["birthday"] else None
                ),
                "group": contact["group"],
                "created_at": (
                    contact["created_at"].isoformat() if contact["created_at"] else None
                ),
                "phones": contact["phones"],
            }
        )

    try:
        with json_path.open("w", encoding="utf-8") as json_file:
            json.dump(payload, json_file, ensure_ascii=False, indent=2)
        print(f"Exported {len(payload)} contacts to {json_path}")
    except Exception as error:
        print(f"JSON export error: {error}")


def ask_duplicate_action(name):
    while True:
        choice = input(
            f"Contact '{name}' already exists. Type 'skip' or 'overwrite': "
        ).strip().lower()
        if choice in {"skip", "overwrite"}:
            return choice
        print("Please type skip or overwrite.")


def import_from_json(filename):
    json_path = resolve_path(filename)
    if not json_path.exists():
        print(f"JSON file not found: {json_path}")
        return

    conn = get_connection()
    if not conn:
        return

    try:
        with json_path.open("r", encoding="utf-8") as json_file:
            data = json.load(json_file)

        inserted = 0
        overwritten = 0
        skipped = 0

        with conn, conn.cursor() as cur:
            for entry in data:
                name = str(entry.get("name", "")).strip()
                if not name:
                    continue

                email = (entry.get("email") or "").strip() or None
                birthday = parse_birthday(entry.get("birthday"))
                group_name = normalize_group_name(entry.get("group"))
                phones = normalize_phone_list(
                    entry.get("phones"),
                    fallback_phone=entry.get("phone"),
                    fallback_type=entry.get("phone_type"),
                )

                contact_id = find_single_contact_id(cur, name)

                if contact_id:
                    action = ask_duplicate_action(name)
                    if action == "skip":
                        skipped += 1
                        continue

                    replace_contact(
                        cur,
                        contact_id,
                        name,
                        email,
                        birthday,
                        group_name,
                        phones,
                    )
                    overwritten += 1
                else:
                    create_contact(cur, name, email, birthday, group_name, phones)
                    inserted += 1

        print(
            "JSON import finished. "
            f"Inserted: {inserted}, overwritten: {overwritten}, skipped: {skipped}"
        )
    except Exception as error:
        print(f"JSON import error: {error}")
    finally:
        conn.close()


def search_all_fields():
    query = input("Enter name, email, or phone fragment: ").strip()
    if not query:
        print("Search text cannot be empty.")
        return

    conn = get_connection()
    if not conn:
        return

    try:
        with conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM search_contacts(%s)", (query,))
            rows = cur.fetchall()
    except Exception as error:
        print(f"Search error: {error}")
        conn.close()
        return
    finally:
        if not conn.closed:
            conn.close()

    contacts_map = {}
    for row in rows:
        contact_id = row[0]
        if contact_id not in contacts_map:
            contacts_map[contact_id] = {
                "id": contact_id,
                "name": row[1],
                "email": row[2],
                "birthday": row[3],
                "group": row[4],
                "created_at": row[7],
                "phones": [],
            }

        if row[5] and row[5] not in {
            item["phone"] for item in contacts_map[contact_id]["phones"]
        }:
            contacts_map[contact_id]["phones"].append(
                {"phone": row[5], "type": row[6] or "mobile"}
            )

    print_contacts(list(contacts_map.values()))


def add_phone_to_contact():
    name = input("Contact name: ").strip()
    phone = input("New phone number: ").strip()
    phone_type = input("Phone type (home/work/mobile): ").strip()

    if not name or not phone:
        print("Name and phone are required.")
        return

    try:
        phone_type = normalize_phone_type(phone_type)
    except ValueError as error:
        print(error)
        return

    conn = get_connection()
    if not conn:
        return

    try:
        with conn, conn.cursor() as cur:
            cur.execute("CALL add_phone(%s, %s, %s)", (name, phone, phone_type))
        print("Phone number added.")
    except Exception as error:
        print(f"Could not add phone: {error}")
    finally:
        conn.close()


def move_contact_to_group():
    name = input("Contact name: ").strip()
    group_name = input("New group: ").strip()

    if not name or not group_name:
        print("Name and group are required.")
        return

    conn = get_connection()
    if not conn:
        return

    try:
        with conn, conn.cursor() as cur:
            cur.execute("CALL move_to_group(%s, %s)", (name, group_name))
        print("Contact group updated.")
    except Exception as error:
        print(f"Could not move contact: {error}")
    finally:
        conn.close()


def paginated_view():
    raw_limit = input("Page size (default 5): ").strip()
    try:
        limit = int(raw_limit) if raw_limit else 5
    except ValueError:
        print("Page size must be a number.")
        return

    if limit <= 0:
        print("Page size must be greater than zero.")
        return
    offset = 0

    conn = get_connection()
    if not conn:
        return

    try:
        with conn, conn.cursor() as cur:
            while True:
                cur.execute(
                    "SELECT * FROM get_contacts_paginated(%s, %s)",
                    (limit, offset),
                )
                rows = cur.fetchall()

                if rows:
                    print(f"\nPage starting from offset {offset}:")
                    for index, row in enumerate(rows, start=1):
                        print(f"{index}. {row[0]} - {row[1]}")
                else:
                    print("\nNo contacts on this page.")

                action = input("Type next, prev, or quit: ").strip().lower()
                if action == "next":
                    if rows:
                        offset += limit
                    else:
                        print("There is no next page.")
                elif action == "prev":
                    offset = max(0, offset - limit)
                elif action == "quit":
                    break
                else:
                    print("Unknown command.")
    except errors.UndefinedFunction:
        print(
            "get_contacts_paginated() is missing. "
            "Load the Practice 08 pagination function first."
        )
    except Exception as error:
        print(f"Pagination error: {error}")
    finally:
        conn.close()


def main():
    while True:
        print("\n--- PHONEBOOK TSIS1 ---")
        print("1. Setup or migrate database")
        print("2. Import contacts from CSV")
        print("3. Import contacts from JSON")
        print("4. Export contacts to JSON")
        print("5. Show contacts with filters and sorting")
        print("6. Search all fields")
        print("7. Add phone to a contact")
        print("8. Move contact to another group")
        print("9. Paginated navigation")
        print("10. Exit")

        choice = input("Choose an action (1-10): ").strip()

        if choice == "1":
            setup_database()
        elif choice == "2":
            filename = input("CSV filename (default contacts.csv): ").strip() or "contacts.csv"
            import_from_csv(filename)
        elif choice == "3":
            filename = input("JSON filename: ").strip()
            if filename:
                import_from_json(filename)
            else:
                print("JSON filename is required.")
        elif choice == "4":
            filename = input("Export filename (default contacts.json): ").strip() or "contacts.json"
            export_to_json(filename)
        elif choice == "5":
            show_contacts_with_filters()
        elif choice == "6":
            search_all_fields()
        elif choice == "7":
            add_phone_to_contact()
        elif choice == "8":
            move_contact_to_group()
        elif choice == "9":
            paginated_view()
        elif choice == "10":
            print("Goodbye.")
            break
        else:
            print("Unknown menu option.")


if __name__ == "__main__":
    main()
