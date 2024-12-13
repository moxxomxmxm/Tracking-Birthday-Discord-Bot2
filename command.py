import discord
from discord.ext import tasks, commands
from datetime import datetime, timedelta
import json
from discord import Embed, Color


DISCORD_TOKEN = # Replace with your bot token
CHANNEL_ID =  # Replace with your channel ID

# Dictionary to store birthdays
birthdays = {}

def save_birthdays():
    """Save birthdays to a JSON file."""
    with open("birthdays.json", "w") as f:
        json.dump(
            {k: {"date": v["date"].strftime('%Y-%m-%d'), "relationship": v.get("relationship", "other")}
             for k, v in birthdays.items()},
            f
        )

def load_birthdays():
    """Load birthdays from a JSON file."""
    global birthdays
    try:
        with open("birthdays.json", "r") as f:
            data = json.load(f)
            birthdays = {k: {"date": datetime.strptime(v["date"], "%Y-%m-%d"), "relationship": v["relationship"]} for k, v in data.items()}
    except FileNotFoundError:
        birthdays = {}

# Bot setup
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Required for privileged intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Event for when the bot is ready
@bot.event
async def on_ready():
    load_birthdays()
    print(f"Logged in as {bot.user}")
    try:
        await bot.tree.sync()
        print("Slash commands synced successfully!")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    if not birthday_reminder.is_running():
        birthday_reminder.start()


# Slash commands
@bot.tree.command(name="add_birthday", description="Add a friend's birthday.")
async def add_birthday(interaction: discord.Interaction, friend_name: str, date: str, relationship: str = "other"):
    """Add a friend's birthday."""
    try:
        birthday_date = datetime.strptime(date, "%Y-%m-%d")
        birthdays[friend_name] = {"date": birthday_date, "relationship": relationship}
        save_birthdays()
        await interaction.response.send_message(f"🎉 Added {friend_name}'s birthday on {date} with relationship '{relationship}'.")
    except ValueError:
        await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD.", ephemeral=True)

@bot.tree.command(name="remove_birthday", description="Remove a friend's birthday.")
async def remove_birthday(interaction: discord.Interaction, friend_name: str):
    """Remove a friend's birthday."""
    if friend_name in birthdays:
        del birthdays[friend_name]
        save_birthdays()
        await interaction.response.send_message(f"Removed {friend_name}'s birthday.")
    else:
        await interaction.response.send_message(f"No birthday found for {friend_name}.", ephemeral=True)

from discord import Embed, Color

from discord import Embed, Color

from discord import Embed, Color

from discord import Embed, Color

@bot.tree.command(name="check_all_birthdays", description="Display all stored birthdays categorized by relationship.")
async def check_all_birthdays(interaction: discord.Interaction):
    """Display all birthdays in one message with different colors for each category."""
    try:
        # Defer the response to allow processing time
        await interaction.response.defer(thinking=True)

        # Define categorized birthdays and colors
        categorized_birthdays = {
            "family": {"entries": [], "color": Color.red()},
            "DA friend": {"entries": [], "color": Color.blue()},
            "TP friend": {"entries": [], "color": Color.green()},
            "other": {"entries": [], "color": Color.purple()}
        }

        # Organize birthdays into categories
        for name, details in birthdays.items():
            date = details["date"]
            relationship = details.get("relationship", "other")
            age_text = calculate_age(date)

            # Add each entry to its respective category
            if relationship not in categorized_birthdays:
                relationship = "other"

            categorized_birthdays[relationship]["entries"].append(
                f"**{name}**\nDate: {date.strftime('%Y-%m-%d')}\n{age_text}"
            )

        # Combine embeds for each category into one message
        embeds = []
        for category, data in categorized_birthdays.items():
            if data["entries"]:  # Only include non-empty categories
                embed = Embed(
                    title=f"{category.capitalize()} Birthdays",
                    description="\n\n".join(data["entries"]),
                    color=data["color"]
                )
                embeds.append(embed)

        # Send all embeds in a single followup response
        if embeds:
            await interaction.followup.send(embeds=embeds)
        else:
            await interaction.followup.send("No birthdays found.")

    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


# Helper function to calculate the age
def calculate_age(birth_date):
    today = datetime.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        return f"current age: {age - 1}, incoming age: {age}"
    return f"current age: {age}, incoming age: {age + 1}"

@bot.tree.command(name="help", description="List all available slash commands.")
async def help_command(interaction: discord.Interaction):
    """Generate a help message listing all slash commands."""
    commands_list = bot.tree.get_commands()
    help_message = "**Available Slash Commands:**\n"
    for command in commands_list:
        help_message += f"/{command.name} - {command.description}\n"
    
    await interaction.response.send_message(help_message, ephemeral=True)



# Helper function to calculate age
def calculate_age(birth_date):
    today = datetime.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        return f"current age: {age - 1}, incoming age: {age}"
    return f"current age: {age}, incoming age: {age + 1}"

# Scheduled task for reminders
@tasks.loop(hours=24)
async def birthday_reminder():
    today = datetime.today()
    reminder_start = today
    reminder_end = today + timedelta(weeks=2)

    upcoming_birthdays = []
    for name, details in birthdays.items():
        birthday_this_year = details["date"].replace(year=today.year)
        if reminder_start <= birthday_this_year <= reminder_end:
            age = today.year - details["date"].year
            upcoming_birthdays.append(f"{name} (Turning {age})")

    if upcoming_birthdays:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(f"🎉 Upcoming birthdays:\n" + "\n".join(upcoming_birthdays))
        user = await bot.fetch_user(1107519870180012135)  # Replace with your numeric user ID
        if user:
            try:
                await user.send(f"🎉 Upcoming birthdays:\n" + "\n".join(upcoming_birthdays))
            except discord.Forbidden:
                print("Unable to send DM to the user.")

@bot.tree.command(name="test_message", description="Send a test message.")
async def test_message(interaction: discord.Interaction):
    """Send test messages."""
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("This is a test message to the server channel.")
    try:
        await interaction.user.send("This is a test DM.")
    except discord.Forbidden:
        await interaction.response.send_message("Unable to send DM.", ephemeral=True)
    await interaction.response.send_message("Test messages sent.")

# Run the bot
bot.run(DISCORD_TOKEN)
