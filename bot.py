import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from discord import app_commands
from db import (
    setup_database,
    save_server_settings,
    get_server_settings,
    add_timezone_member,
    remove_timezone_member,
    get_timezone_members,
    get_timezone_member,
    update_member_details,
    update_member_timezone,
    reset_member_details
)

import discord
from discord.ui import Modal, TextInput
from discord.ext import tasks

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = 1484957940749438986
DATA_FILE = "bot_data.json"

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

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


def build_timezone_embed(guild_id):
    now_utc = datetime.now(ZoneInfo("UTC"))

    timezone_rows = get_timezone_members(guild_id)

    timezones = []

    for  row in timezone_rows:
        if not row[5]:
            continue

        activity = row[6] or "Around"
        availability = row[7] or "Available"

        if row [10]:
            activity = row[8] or activity
            availability = row[7] or availability

        timezones.append({
            "name": row[1],
            "emoji": row[3],
            "label": row[4],
            "tz": row[5],
            "activity": activity,
            "availability": availability
        })

    entries = []

    for entry in timezones:
        local_time = now_utc.astimezone(ZoneInfo(entry["tz"]))
        time_str = local_time.strftime("%I:%M %p").lstrip("0")
        day_str = local_time.strftime("%a")
        status = get_status(local_time)

        entries.append({
    "sort_date": local_time.date(),
    "sort_time": local_time.time(),
    "name": f'{entry["emoji"]}   {entry["name"]}\n[{entry["label"]}]',
    "value": f'🕒 **{time_str}** ({day_str})\n{status}\n🟢 {entry['activity']} • {entry['availability']}\n────────\n\u200b'
})

    entries.sort(key=lambda x: (x["sort_date"], x["sort_time"], x["name"]))

    embed = discord.Embed(
    title="🌍 Current Times",
    description="Times updated automatically",
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
    await tree.sync()
    print("Slash commands synced.")
    print(f"Logged in as {client.user}")
    if not update_timezones.is_running():
        update_timezones.start()


@tasks.loop(minutes=1)
async def update_timezones():
    for guild in client.guilds:
        settings = get_server_settings(guild.id)

        if not settings:
            continue

        channel_id = settings["channel_id"]
        message_id = settings["message_id"]

        channel = client.get_channel(channel_id)

        if channel is None:
            channel = await client.fetch_channel(channel_id)

        embed = build_timezone_embed(guild.id)

        if message_id:
            try:
                message = await channel.fetch_message(message_id)
                await message.edit(content=None, embed=embed)
                print(f"Updated timezone message for {guild.name}.")
                continue
            except discord.NotFound:
                print(f"Old message not found for {guild.name}. Sending a new one.")

        new_message = await channel.send(embed=embed)

        save_server_settings(
            guild.id,
            channel_id,
            new_message.id
        )

        print(f"Sent new timezone message for {guild.name}.")


@update_timezones.before_loop
async def before_update_timezones():
    await client.wait_until_ready()

if not TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN is not set.")


# Slash Commands
@tree.command(name="timezone_setup", description="Set the timezone channel")
@app_commands.checks.has_permissions(administrator=True)
async def timezone_setup(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.send_message(
        f"Timezone channel set to {channel.mention}",
        ephemeral=True
    )

    save_server_settings(
        interaction.guild.id,
        channel.id
    )

def country_to_flag(country):
    countries = {
        "australia": "🇦🇺",
        "united states": "🇺🇸",
        "usa": "🇺🇸",
        "america": "🇺🇸",
        "united kingdom": "🇬🇧",
        "uk": "🇬🇧",
        "england": "🇬🇧",
        "scotland": "🇬🇧",
        "ireland": "🇮🇪",
        "canada": "🇨🇦",
        "new zealand": "🇳🇿",
        "philippines": "🇵🇭",
        "indonesia": "🇮🇩",
        "germany": "🇩🇪",
        "spain": "🇪🇸",
        "mexico": "🇲🇽",
        "austria": "🇦🇹"
    }

    value = country.strip().lower()

    return countries.get(value, country)

class TimezoneAddModal(discord.ui.Modal, title="Set Up Timezone Profile"):
    display_name = discord.ui.TextInput(
        label="Display name",
        placeholder="✨John Smith",
        required=True
    )

    age = discord.ui.TextInput(
        label="Age",
        placeholder="00",
        required=True
    )

    flag = discord.ui.TextInput(
        label="Flag",
        placeholder="Country",
        required=True
    )

    location = discord.ui.TextInput(
        label="Location",
        placeholder="State, Country",
        required=True
    )

    timezone = discord.ui.TextInput(
        label="Timezone",
        placeholder="Timezone",
        required=True
    )

    def __init__(self, user):
        super().__init__()
        self.user = user

    async def on_submit(self, interaction: discord.Interaction):
        timezone_value = str(self.timezone).strip()
        timezone_valid = True

        try:
            ZoneInfo(timezone_value)
        except Exception:
            timezone_valid = False
            await interaction.response.send_message(
                f"'{timezone_value}' is not a valid timezone.\n\n"
                f"Example: 'Australia/Brisbane'",
                ephemeral=True
            )
            timezone_value = None
        
        update_member_details(
            interaction.guild.id,
            self.user.id,
            str(self.display_name),
            int(str(self.age)),
            country_to_flag(str(self.flag)),
            str(self.location),
            timezone_value,
            timezone_valid
        )

        await interaction.response.send_message(
            f"Added {self.display_name} to the timezone list.",
            ephemeral=True
        )

class TimezoneEditModal(Modal, title="Edit Timezone Profile"):

    def __init__(self, user, member_data):
        super().__init__()
        self.user = user
        self.member_data = member_data

        self.display_name.default = member_data[1] or ""
        self.age.default = str(member_data[2] or "")
        self.flag.default = member_data[3] or ""
        self.location.default = member_data[4] or ""
        self.timezone.default = member_data[5] or ""

    display_name = TextInput(
        label="Display Name",
        max_length=32,
        required=True
    )

    age = TextInput(
        label="Age",
        max_length=3,
        required=True
    )

    flag = TextInput(
        label="Flag / Country",
        max_length=50,
        required=True
    )

    location = TextInput(
        label="Location",
        max_length=100,
        required=True
    )

    timezone = TextInput(
        label="Timezone",
        max_length=100,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):

        timezone_value = str(self.timezone).strip()
        timezone_valid = True

        try:
            ZoneInfo(timezone_value)
        except Exception:
            timezone_valid = False
            timezone_value = None

        update_member_details(
            interaction.guild.id,
            self.user.id,
            str(self.display_name),
            int(str(self.age)),
            country_to_flag(str(self.flag)),
            str(self.location),
            timezone_value,
            timezone_valid
        )

        await interaction.response.send_message(
            f"{self.user.mention}'s profile was updated!   😄",
            ephemeral=True
        )

        await update_timezones()

@tree.command(name="timezone_add", description="Approve a member for the timezone board")
@app_commands.checks.has_permissions(administrator=True)
async def timezone_add(
    interaction: discord.Interaction,
    user: discord.Member
):
    await interaction.response.send_message(
        f"{user.mention} has been added to the Timezone board setup list.\n"
        f"Use '/timezone_my_details' to set up your profile.\n\n"
        f"*Want to join the board?   Conact an admin to be added!   😊*"
    )

    existing_member = get_timezone_member(
        interaction.guild.id,
        user.id
    )

    if existing_member:
        await interaction.response.send_message(
            f"{user.mention} is already on this timezone board.",
            ephemeral=True
        )
        return

    add_timezone_member(
        interaction.guild.id,
        user.id
    )

@tree.command(name="timezone_reset_details", description="Reset a member's timezone profile lock")
@app_commands.checks.has_permissions(administrator=True)
async def timezone_reset_details(
    interaction: discord.Interaction,
    user: discord.Member
):
    member = get_timezone_member(
        interaction.guild.id,
        user.id
    )

    if not member:
        await interaction.response.send_message(
            f"{user.mention} is not on this timezone board.",
            ephemeral=True
        )
        return
    
    reset_member_details(
        interaction.guild.id,
        user.id
    )

    await interaction.response.send_message(
        f"{user.mention}'s timezone profile has been unlocked!",
        ephemeral=True
    )

@tree.command(name="timezone_edit", description="Edit a member's timezone profile")
@app_commands.checks.has_permissions(administrator=True)
async def timezone_edit(
    interaction: discord.Interaction,
    user: discord.Member
):
    member = get_timezone_member(
        interaction.guild.id,
        user.id
    )

    if not member:
        await interaction.response.send_message(
            f"{user.mention} is not on this timezone board.",
            ephemeral=True
        )
        return
    
    await interaction.response.send_modal(
        TimezoneEditModal(user, member)
    )

@tree.command(name="timezone_my_details", description="Set up your timezone profile")
async def timezone_my_details(interaction: discord.Interaction):

    member = get_timezone_member(
        interaction.guild.id,
        interaction.user.id
    )

    if not member:
        await interaction.response.send_message(
            f"You are not on the timezone setup list.\n\n"
            f"*Want to join the board?   Contact an admin to be added!   😊*",
            ephemeral=True
        )
        return
    
    if member[6]:
        await interaction.response.send_message(
            "your timezone profile is already locked. Contact an admin if you need changes.",
            ephemeral=True
        )
        return
    
    await interaction.response.send_modal(
        TimezoneAddModal(interaction.user)
    )

@tree.command(name="timezone_set_timezone", description="Set or fix your timezone")
async def timezone_set_timezone(
    interaction: discord.Interaction,
    timezone: str
):
    
    try:
        ZoneInfo(timezone)
    except Exception:
        await interaction.response.send_message(
            f"'{timezone}' is not a valid timezone.\n\n"
            f"Example: 'Australia/Brisbane'",
            ephemeral=True
        )
        return
    
    update_member_timezone(
        interaction.guild.id,
        interaction.user.id,
        timezone
    )

    await interaction.response.send_message(
        f"Timezone updated to '{timezone}'   😄",
        ephemeral=True
    )

    await update_timezones()

@tree.command(name="timezone_remove", description="Remove a person from the timezone list")
@app_commands.checks.has_permissions(administrator=True)
async def timezone_remove(
    interaction: discord.Interaction,
    user: discord.Member
):
    await interaction.response.send_message(
        f"Removed {user.mention} from the timezone list.",
        ephemeral=True
    )

    remove_timezone_member(
        interaction.guild.id,
        user.id
    )

@tree.command(name="timezone_list", description="Show timezone members")
async def timezone_list(interaction: discord.Interaction):

    members = get_timezone_members(interaction.guild.id)

    if not members:
        await interaction.response.send_message(
            "No timezone members saved.",
            ephemeral=True
        )
        return
    
    lines = []

    for member in members:
        lines.append(
            f"{member[3]} {member[1]} - {member[4]} ({member[5]})"
        )

    message = "\n".join(lines)

    await interaction.response.send_message(
        message,
        ephemeral=True
    )

@tree.command(name="timezone_refresh", description="Refresh the timezone embed")
@app_commands.checks.has_permissions(administrator=True)
async def timezone_refresh(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Refreshing timezone board...",
        ephemeral=True
    )

    await update_timezones()

    await interaction.followup.send(
        "Timezone board refreshed.",
        ephemeral=True
    )

@tree.command(name="timezone_help", description="Show timezone bot help")
async def timezone_help(interaction: discord.Interaction):

    await interaction.response.send_message(
        "**Timezone Bot Help**\n\n"
        "**Members:**"
        "'/timezone_my_details' - Set up your profile after an admin adds you.\n"
        "'/timezone_set_timezone' - Fix your timezone if needed.\n\n"
        "**Admins:**\n"
        "'/timezone_add' - Add/approve a memmber.\n"
        "'/timezone_remove' - Remove a member.\n"
        "'/timezone_edit' - Edit a member profile.\n"
        "'/timezone_reset_details' - Let a member redo their profile.\n"
        "'/timezone_refresh' - Refresh the timezone board.\n\n"
        "**Timezone Examples:**\n"
        "'Australia/Brisbane'\n"
        "'America/New_York'\n"
        "'Europe/London'\n"
        "'Asia/Manila'\n\n"
        "**Tip:** You can type a country name like 'Australia' instead of a flag emoji.",
        ephemeral=True
    )

setup_database()
client.run(TOKEN)