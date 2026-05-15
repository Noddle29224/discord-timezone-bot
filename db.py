import os
import psycopg

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg.connect(DATABASE_URL)

def setup_database():
    with get_connection() as conn:
        with conn.cursor() as cur:

            # Server settings table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS server_settings (
                    guild_id BIGINT PRIMARY KEY,
                    channel_id BIGINT,
                    message_id BIGINT
                )
            """)

            # Timezone members table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS timezone_members (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    display_name TEXT,
                    age INTEGER,
                    flag TEXT,
                    location TEXT,
                    timezone TEXT,
                    details_locked BOOLEAN DEFAULT FALSE,
                    availability_locked BOOLEAN DEFAULT FALSE,
                    manual_override_enabled BOOLEAN DEFAULT FALSE,
                    manual_activity TEXT,
                    manual_availability TEXT
                )
            """)

        conn.commit()

    print("Database setup complete.")

def save_server_settings(guild_id, channel_id, message_id=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO server_settings (guild_id, channel_id, message_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (guild_id)
                DO UPDATE SET
                    channel_id = EXCLUDED.channel_id,
                    message_id = EXCLUDED.message_id
            """, (guild_id, channel_id, message_id))

        conn.commit()

def get_server_settings(guild_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT channel_id, message_id
                FROM server_settings
                WHERE guild_id = %s
            """, (guild_id,))

            result = cur.fetchone()

            if result:
                return {
                    "channel_id": result[0],
                    "message_id": result[1]
                }
            return None

def add_timezone_member(
    guild_id,
    user_id,
    display_name=None,
    age=None,
    flag=None,
    location=None,
    timezone=None
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO timezone_members (
                    guild_id,
                    user_id,
                    display_name,
                    age,
                    flag,
                    location,
                    timezone
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                guild_id,
                user_id,
                display_name,
                age,
                flag,
                location,
                timezone
            ))

        conn.commit()

def remove_timezone_member(guild_id, user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM timezone_members
                WHERE guild_id = %s
                AND user_id = %s
            """, (guild_id, user_id))

        conn.commit()

def get_timezone_members(guild_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    user_id,
                    display_name,
                    age,
                    flag,
                    location,
                    timezone
                FROM timezone_members
                WHERE guild_id = %s
                ORDER BY location
            """, (guild_id,))

            rows = cur.fetchall()

            return rows
