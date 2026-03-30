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
        return "🌙 Asleep"
    elif 6 <= hour < 9:
        return "🌅 Up soon"
    elif 9 <= hour < 22:
        return "☀️ Awake"
    else:
        return "🌃 Late"


def build_timezone_embed():
    now_utc = datetime.now(ZoneInfo("UTC"))

    timezones = [
    {"name": "💙 ℂ𝕙𝕒𝕣𝕝𝕚𝕖 [23]", "emoji": "🇦🇺", "label": "Queensland, Australia", "tz": "Australia/Brisbane"},
    {"name": "💚 ℂ𝕙𝕣𝕚𝕤 [26]", "emoji": "🇺🇸", "label": "California, USA", "tz": "America/Los_Angeles"},
    {"name": "💛 𝕃𝕦𝕜𝕖 [23]", "emoji": "🇦🇺", "label": "South Australia", "tz": "Australia/Adelaide"},
    {"name": "❤️ ℕ𝕚𝕔𝕜 [27]", "emoji": "🇺🇸", "label": "North Carolina, USA", "tz": "America/New_York"},
    {"name": "💖 𝕄𝕒𝕥𝕥 [43]", "emoji": "🇺🇸", "label": "Virginia, USA", "tz": "America/New_York"},
    {"name": "🖤 ℕ𝕚𝕟𝕔𝕙𝕚 [32]", "emoji": "🇺🇸", "label": "California, USA", "tz": "America/Los_Angeles"},
    {"name": "🤍 𝕄𝕦𝕜𝕖𝕤𝕙 [24]", "emoji": "🇺🇸", "label": "Texas, USA", "tz": "America/Chicago"},
    {"name": "🩵 𝕊𝕥𝕖𝕧𝕖𝕟 [25]", "emoji": "🇺🇸", "label": "Idaho, USA", "tz": "America/Denver"},
    {"name": "🧡 ℝ𝕖𝕘 [32]", "emoji": "🇺🇸", "label": "Massachusetts, USA", "tz": "America/New_York"},
    {"name": "💜 𝔻𝕠𝕧𝕖 [30]", "emoji": "🇮🇩", "label": "Bandung, Indonesia", "tz": "Asia/Jakarta"},
    {"name": "🩶 𝔸𝕕𝕖𝕟 [23]", "emoji": "🇬🇧", "label": "Edinburgh, Scotland", "tz": "Europe/London"},
    {"name": "🩷 𝕍𝕚 [26]", "emoji": "🇪🇸", "label": "Spain", "tz": "Europe/Madrid"},
    {"name": "🤎 𝕋𝕒𝕪𝕝𝕠𝕣 [30]", "emoji": "🇺🇸", "label": "Kentucky, USA", "tz": "America/New_York"},
]

    entries = []

    for entry in timezones:
        local_time = now_utc.astimezone(ZoneInfo(entry["tz"]))
        time_str = local_time.strftime("%I:%M %p").lstrip("0")
        day_str = local_time.strftime("%a")
        status = get_status(local_time)

        entries.append({
    "sort_date": local_time.date(),
    "sort_time": local_time.time(),
    "name": f'{entry["emoji"]} {entry["name"]}\n[{entry["label"]}]',
    "value": f'🕒 **{time_str}** ({day_str})\n{status}\n────────\n\u200b'
})

    entries.sort(key=lambda x: (x["sort_date"], x["sort_time"], x["name"]))

    embed = discord.Embed(
    title="🌍 Current Times",
    description="Updated automatically every 30 minutes",
    color=0x5865F2  # Discord blurple
)

    for item in entries:
        embed.add_field(
            name=item["name"],
            value=item["value"],
            inline=True
        )

    # pad final row so embed layout stays neat
    remainder = len(entries) % 3
    if remainder != 0:
        for _ in range(3 - remainder):
            embed.add_field(name="\u200b", value="\u200b", inline=True)

    embed.set_footer(text=f"Last updated: {now_utc.strftime('%d %b %Y, %H:%M UTC')}")
    return embed


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

    embed = build_timezone_embed()
    message_id = data.get("message_id")

    if message_id:
        try:
            message = await channel.fetch_message(message_id)
            await message.edit(content=None, embed=embed)
            print("Updated existing timezone message.")
            return
        except discord.NotFound:
            print("Old message not found. Sending a new one.")
        except discord.Forbidden:
            print("Bot does not have permission.")
        except discord.HTTPException as e:
            print(f"Discord error: {e}")

    new_message = await channel.send(embed=embed)
    data["message_id"] = new_message.id
    save_data(data)
    print("Sent new timezone message.")


@update_timezones.before_loop
async def before_update_timezones():
    await client.wait_until_ready()

if not TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN is not set.")

client.run(TOKEN)