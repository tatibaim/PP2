from pathlib import Path

import psycopg2

from config import load_config


BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / "schema.sql"


class SnakeDatabase:
    def __init__(self):
        self._config = load_config()

    def connect(self):
        return psycopg2.connect(**self._config)

    def init_db(self):
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(SCHEMA_PATH.read_text(encoding="utf-8"))

    def get_or_create_player_id(self, username):
        clean_name = username.strip()[:50] or "Player"
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO players (username)
                VALUES (%s)
                ON CONFLICT (username) DO UPDATE
                SET username = EXCLUDED.username
                RETURNING id
                """,
                (clean_name,),
            )
            return cur.fetchone()[0]

    def save_session(self, username, score, level_reached):
        player_id = self.get_or_create_player_id(username)
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO game_sessions (player_id, score, level_reached)
                VALUES (%s, %s, %s)
                """,
                (player_id, int(score), int(level_reached)),
            )

    def fetch_personal_best(self, username):
        clean_name = username.strip()[:50] or "Player"
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT COALESCE(MAX(gs.score), 0)
                FROM game_sessions gs
                JOIN players p ON p.id = gs.player_id
                WHERE p.username = %s
                """,
                (clean_name,),
            )
            row = cur.fetchone()
            return int(row[0] or 0)

    def fetch_top_scores(self, limit=10):
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    p.username,
                    gs.score,
                    gs.level_reached,
                    gs.played_at
                FROM game_sessions gs
                JOIN players p ON p.id = gs.player_id
                ORDER BY gs.score DESC, gs.level_reached DESC, gs.played_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()
