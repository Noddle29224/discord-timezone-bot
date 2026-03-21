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

    cells = []

    for entry in timezones:
        local_time = now_utc.astimezone(ZoneInfo(entry["tz"]))
        time_str = local_time.strftime("%I:%M %p").lstrip("0")
        day_str = local_time.strftime("%a")

        title = f'[{entry["tag"]}] {entry["label"]}'
        time_line = f'{time_str} ({day_str})'
        cells.append((title, time_line))

    col_width = 24
    lines = ["Current Times", ""]

    for i in range(0, len(cells), 3):
        row = cells[i:i+3]

        title_line = ""
        time_line = ""

        for title, time_text in row:
            title_line += f"{title:<{col_width}}"
            time_line += f"{time_text:<{col_width}}"

        lines.append(title_line.rstrip())
        lines.append(time_line.rstrip())
        lines.append("")

    return "```\n" + "\n".join(lines) + "\n```"


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    if not update_timezones.is_running():
        update_timezones.start()


@tasks.loop(minutes=30)
async def update_timezones():
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
            print("Bot does not have permission to edit/fetch the message.")
        except discord.HTTPException as e:
            print(f"Discord error while editing message: {e}")

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