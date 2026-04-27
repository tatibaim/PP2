from pathlib import Path

import psycopg2

from config import load_config


BASE_DIR = Path(__file__).resolve().parent


def execute_sql_file(cursor, filename):
    sql_path = BASE_DIR / filename
    if not sql_path.exists():
        print(f"SQL file not found: {sql_path}")
        return

    with sql_path.open("r", encoding="utf-8") as sql_file:
        cursor.execute(sql_file.read())


def setup_database():
    conn = None

    try:
        conn = psycopg2.connect(**load_config())
        with conn, conn.cursor() as cur:
            execute_sql_file(cur, "schema.sql")
            execute_sql_file(cur, "procedures.sql")

            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM pg_proc
                    WHERE proname = 'get_contacts_paginated'
                )
                """
            )
            has_pagination = cur.fetchone()[0]

        print("Database schema and TSIS1 procedures were applied successfully.")
        if not has_pagination:
            print(
                "Note: get_contacts_paginated() was not found. "
                "The paginated console view expects the Practice 08 function."
            )
    except Exception as error:
        print(f"Database setup error: {error}")
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    setup_database()
