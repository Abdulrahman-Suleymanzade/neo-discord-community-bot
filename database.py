import sqlite3
import time
from pathlib import Path
from leveling import calculate_level

DB_PATH = Path("data/users.db")
COOLDOWN_SECONDS = 20


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                xp INTEGER NOT NULL DEFAULT 0,
                last_xp_time INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            )
        """)


def add_xp(guild_id: int, user_id: int, username: str, xp_amount: int):
    now = int(time.time())

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT xp, last_xp_time FROM users WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        row = cursor.fetchone()

        if row is None:
            old_xp = 0
            old_level = 0
            cursor.execute(
                "INSERT INTO users (guild_id, user_id, username, xp, last_xp_time) VALUES (?, ?, ?, ?, ?)",
                (guild_id, user_id, username, xp_amount, now),
            )
            new_xp = xp_amount
        else:
            old_xp, last_xp_time = row
            if now - last_xp_time < COOLDOWN_SECONDS:
                return {"leveled_up": False, "new_level": calculate_level(old_xp)}

            old_level = calculate_level(old_xp)
            new_xp = old_xp + xp_amount
            cursor.execute(
                "UPDATE users SET username = ?, xp = ?, last_xp_time = ? WHERE guild_id = ? AND user_id = ?",
                (username, new_xp, now, guild_id, user_id),
            )

        new_level = calculate_level(new_xp)
        return {"leveled_up": new_level > old_level, "new_level": new_level}


def set_user_xp(guild_id: int, user_id: int, username: str, xp: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT xp FROM users WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        row = cursor.fetchone()

        if row is None:
            cursor.execute(
                "INSERT INTO users (guild_id, user_id, username, xp, last_xp_time) VALUES (?, ?, ?, ?, ?)",
                (guild_id, user_id, username, xp, int(time.time())),
            )
        else:
            cursor.execute(
                "UPDATE users SET username = ?, xp = ? WHERE guild_id = ? AND user_id = ?",
                (username, xp, guild_id, user_id),
            )

        return {"xp": xp, "level": calculate_level(xp)}


def get_user_rank(guild_id: int, user_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, xp FROM users WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
        user = cursor.fetchone()

        if not user:
            return None

        cursor.execute("SELECT COUNT(*) + 1 FROM users WHERE guild_id = ? AND xp > ?", (guild_id, user[1]))
        rank = cursor.fetchone()[0]

        return {"username": user[0], "xp": user[1], "rank": rank}


def get_leaderboard(guild_id: int, limit: int = 10):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username, xp FROM users WHERE guild_id = ? ORDER BY xp DESC LIMIT ?",
            (guild_id, limit),
        )
        return [dict(row) for row in cursor.fetchall()]
