import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord.ext import tasks

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = 1484957940749438986
DATA_FILE = "bot_data.json"

intents = discord.Intents.default()
client = discord.Client(intents=intents)


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"message_id": None}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


def get_status(local_time):
    hour = local_time.hour

    if 0 <= hour < 6:
        return "zzz"
    elif 6 <= hour < 9:
        return "up soon"
    elif 9 <= hour < 22:
        return "awake"
    else:
        return "late"


def build_timezone_text():
    now_utc = datetime.now(ZoneInfo("UTC"))

    timezones = [
        {"tag": "US", "label": "Eastern US", "tz": "America/New_York"},
        {"tag": "AU", "label": "Queensland", "tz": "Australia/Brisbane"},
        {"tag": "US", "label": "Texas", "tz": "America/Chicago"},
        {"tag": "PH", "label": "Philippines", "tz": "Asia/Manila"},
        {"tag": "MX", "label": "Mexico", "tz": "America/Mexico_City"},
        {"tag": "AT", "label": "Austria", "tz": "Europe/Vienna"},
        {"tag": "UK", "label": "UK", "tz": "Europe/London"},
        {"tag": "IE", "label": "Ireland", "tz": "Europe/Dublin"},
        {"tag": "AU", "label": "S. Australia", "tz": "Australia/Adelaide"},
        {"tag": "US", "label": "Southern US", "tz": "America/Chicago"},
        {"tag": "DE", "label": "Germany", "tz": "Europe/Berlin"},
        {"tag": "US", "label": "New York", "tz": "America/New_York"},
        {"tag": "US", "label": "Pennsylvania", "tz": "America/New_York"},
    ]

    entries = []

    for entry in timezones:
        local_time = now_utc.astimezone(ZoneInfo(entry["tz"]))
        time_str = local_time.strftime("%I:%M %p").lstrip("0")
        day_str = local_time.strftime("%a")
        status = get_status(local_time)

        entries.append({
            "sort_hour": local_time.hour,
            "sort_minute": local_time.minute,
            "title": f'[{entry["tag"]}] {entry["label"]}',
            "time_line": f'{time_str} ({day_str})',
            "status_line": f'[{status}]'
        })

    # Sort by local time
    entries.sort(key=lambda x: (x["sort_hour"], x["sort_minute"], x["title"]))

    col_width = 24
    lines = ["Current Times", ""]

    for i in range(0, len(entries), 3):
        row = entries[i:i+3]

        title_line = ""
        time_line = ""
        status_line = ""

        for item in row:
            title_line += f'{item["title"]:<{col_width}}'
            time_line += f'{item["time_line"]:<{col_width}}'
            status_line += f'{item["status_line"]:<{col_width}}'

        lines.append(title_line.rstrip())
        lines.append(time_line.rstrip())
        lines.append(status_line.rstrip())
        lines.append("")

    return "```\n" + "\n".join(lines) + "\n```"


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    if not update_timezones.is_running():
        update_timezones.start()


@tasks.loop(minutes=1)
async def update_timezones():
    now = datetime.now(ZoneInfo("UTC"))

    # Only run at :00 or :30
    if now.minute not in (0, 30):
        return

    data = load_data()

    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        channel = await client.fetch_channel(CHANNEL_ID)

    content = build_timezone_text()
    message_id = data.get("message_id")

    if message_id:
        try:
            message = await channel.fetch_message(message_id)
            await message.edit(content=content)
            print("Updated existing timezone message.")
            return
        except discord.NotFound:
            print("Old message not found. Sending a new one.")
        except discord.Forbidden:
            print("Bot does not have permission.")
        except discord.HTTPException as e:
            print(f"Discord error: {e}")

    new_message = await channel.send(content)
    data["message_id"] = new_message.id
    save_data(data)
    print("Sent new timezone message.")


@update_timezones.before_loop
async def before_update_timezones():
    await client.wait_until_ready()

if not TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN is not set.")

client.run(TOKEN)