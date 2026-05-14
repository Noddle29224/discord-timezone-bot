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
                    timezone TEXT
                )
            """)

        conn.commit()

    print("Database setup complete.")