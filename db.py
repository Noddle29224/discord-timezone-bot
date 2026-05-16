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
                    timezone_valid BOOLEAN DEFAULT FALSE,
                    details_locked BOOLEAN DEFAULT FALSE,
                    availability_locked BOOLEAN DEFAULT FALSE,
                    auto_activity TEXT DEFAULT 'Around',
                    auto_availability TEXT DEFAULT 'Available',
                    sleep_start INTEGER,
                    sleep_end INTEGER,
                    manual_override_enabled BOOLEAN DEFAULT FALSE,
                    manual_activity TEXT,
                    manual_availability TEXT
                )
            """)

            cur.execute("""
                ALTER TABLE timezone_members
                ADD COLUMN IF NOT EXISTS details_locked BOOLEAN DEFAULT FALSE
            """)

            cur.execute("""
                ALTER TABLE timezone_members
                ADD COLUMN IF NOT EXISTS timezone_valid BOOLEAN DEFAULT FALSE
            """)

            cur.execute("""
                ALTER TABLE timezone_members
                ADD COLUMN IF NOT EXISTS auto_activity TEXT DEFAULT 'Around'
            """)

            cur.execute("""
                ALTER TABLE timezone_members
                ADD COLUMN IF NOT EXISTS auto_availability TEXT DEFAULT 'Available'
            """)

            cur.execute("""
                ALTER TABLE timezone_members
                ADD COLUMN IF NOT EXISTS manual_activity TEXT
            """)

            cur.execute("""
                ALTER TABLE timezone_members
                ADD COLUMN IF NOT EXISTS manual_availability TEXT
            """)

            cur.execute("""
                ALTER TABLE timezone_members
                ADD COLUMN IF NOT EXISTS manual_override_enabled BOOLEAN DEFAULT FALSE
            """)

            cur.execute("""
                ALTER TABLE timezone_members
                ADD COLUMN IF NOT EXISTS availability_locked BOOLEAN DEFAULT FALSE
            """)

            cur.execute("""
                ALTER TABLE timezone_members
                ADD COLUMN IF NOT EXISTS sleep_start INTEGER
            """)

            cur.execute("""
                ALTER TABLE timezone_members
                ADD COLUMN IF NOT EXISTS sleep_end INTEGER
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
                    timezone,
                    auto_activity,
                    auto_availability,
                    manual_activity,
                    manual_availability,
                    manual_override_enabled
                FROM timezone_members
                WHERE guild_id = %s
                ORDER BY location
            """, (guild_id,))

            rows = cur.fetchall()

            return rows

def get_timezone_member(guild_id, user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    user_id,
                    display_name,
                    age,
                    flag,
                    location,
                    timezone,
                    details_locked,
                    availability_locked
                FROM timezone_members
                WHERE guild_id = %s
                AND user_id = %s
            """, (guild_id, user_id))

            return cur.fetchone()
        
def update_member_details(
    guild_id,
    user_id,
    display_name,
    age,
    flag,
    location,
    timezone,
    timezone_valid
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE timezone_members
                SET
                    display_name = %s,
                    age = %s,
                    flag = %s,
                    location = %s,
                    timezone = %s,
                    timezone_valid = %s,
                    details_locked = True
                WHERE guild_id = %s
                AND user_id = %s
            """, (
                display_name,
                age,
                flag,
                location,
                timezone,
                timezone_valid,
                guild_id,
                user_id
            ))

        conn.commit()

def update_member_timezone(guild_id, user_id, timezone):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE timezone_members
                SET
                    timezone = %s,
                    timezone_valid = TRUE
                WHERE guild_id = %s
                AND user_id = %s
            """, (
                timezone,
                guild_id,
                user_id
            ))

        conn.commit()

def reset_member_details(guild_id, user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE timezone_members
                SET details_locked = FALSE
                WHERE guild_id = %s
                AND user_id = %s
            """, (
                guild_id,
                user_id
            ))

        conn.commit()

def set_member_override(guild_id, user_id, activity, availability):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE timezone_members
                SET
                    manual_activity = %s,
                    manual_availability = %s,
                    manual_override_enabled = TRUE
                WHERE guild_id = %s
                AND user_id = %s
            """, (
                activity,
                availability,
                guild_id,
                user_id
            ))

        conn.commit()

def set_member_auto_status(guild_id, user_id, activity, availability):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE timezone_members
                SET
                    auto_activity = %s,
                    auto_availability = %s,
                    availability_locked = TRUE
                WHERE guild_id = %s
                AND user_id = %s
            """, (
                activity,
                availability,
                guild_id,
                user_id
            ))

        conn.commit()

def set_sleep_schedule(guild_id, user_id, start_hour, end_hour):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE timezone_members
                SET
                    sleep_start = %s,
                    sleep_end = %s
                WHERE guild_id = %s
                AND user_id = %s
            """, (
                start_hour,
                end_hour,
                guild_id,
                user_id
            ))

        conn.commit()