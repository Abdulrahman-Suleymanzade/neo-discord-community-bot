import os
import time
from urllib.parse import urlparse

import pg8000.dbapi
from dotenv import load_dotenv
from leveling import calculate_level

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
COOLDOWN_SECONDS = 20


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is missing.")

    url = urlparse(DATABASE_URL)

    return pg8000.dbapi.connect(
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port or 5432,
        database=url.path.lstrip("/"),
    )


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                guild_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                username TEXT NOT NULL,
                xp INTEGER NOT NULL DEFAULT 0,
                last_xp_time BIGINT NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        conn.commit()


def add_xp(guild_id: int, user_id: int, username: str, xp_amount: int):
    now = int(time.time())

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT xp, last_xp_time FROM users WHERE guild_id = %s AND user_id = %s",
            (guild_id, user_id),
        )
        row = cursor.fetchone()

        if row is None:
            old_xp = 0
            old_level = 0
            new_xp = xp_amount
            cursor.execute(
                "INSERT INTO users (guild_id, user_id, username, xp, last_xp_time) VALUES (%s, %s, %s, %s, %s)",
                (guild_id, user_id, username, new_xp, now),
            )
        else:
            old_xp, last_xp_time = row

            if now - last_xp_time < COOLDOWN_SECONDS:
                return {"leveled_up": False, "new_level": calculate_level(old_xp)}

            old_level = calculate_level(old_xp)
            new_xp = old_xp + xp_amount
            cursor.execute(
                "UPDATE users SET username = %s, xp = %s, last_xp_time = %s WHERE guild_id = %s AND user_id = %s",
                (username, new_xp, now, guild_id, user_id),
            )

        conn.commit()
        new_level = calculate_level(new_xp)
        return {"leveled_up": new_level > old_level, "new_level": new_level}


def set_user_xp(guild_id: int, user_id: int, username: str, xp: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT xp FROM users WHERE guild_id = %s AND user_id = %s",
            (guild_id, user_id),
        )
        row = cursor.fetchone()

        if row is None:
            cursor.execute(
                "INSERT INTO users (guild_id, user_id, username, xp, last_xp_time) VALUES (%s, %s, %s, %s, %s)",
                (guild_id, user_id, username, xp, int(time.time())),
            )
        else:
            cursor.execute(
                "UPDATE users SET username = %s, xp = %s WHERE guild_id = %s AND user_id = %s",
                (username, xp, guild_id, user_id),
            )

        conn.commit()
        return {"xp": xp, "level": calculate_level(xp)}


def get_user_rank(guild_id: int, user_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username, xp FROM users WHERE guild_id = %s AND user_id = %s",
            (guild_id, user_id),
        )
        user = cursor.fetchone()

        if not user:
            return None

        cursor.execute(
            "SELECT COUNT(*) + 1 FROM users WHERE guild_id = %s AND xp > %s",
            (guild_id, user[1]),
        )
        rank = cursor.fetchone()[0]

        return {"username": user[0], "xp": user[1], "rank": rank}


def get_leaderboard(guild_id: int, limit: int = 10, offset: int = 0):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT username, xp
            FROM users
            WHERE guild_id = %s
            ORDER BY xp DESC
            LIMIT %s OFFSET %s
            """,
            (guild_id, limit, offset),
        )

        rows = cursor.fetchall()
        return [{"username": row[0], "xp": row[1]} for row in rows]
