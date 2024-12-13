from discord.ext import commands, tasks
import discord
from datetime import datetime, timedelta
import json
import requests
import asyncio



DISCORD_TOKEN = #place discord token here
CHANNEL_ID = #place discord channel id here

# Dictionary to store birthdays


birthdays = {}

def save_birthdays():
    # Save birthdays to JSON with date and relationship information
    with open("birthdays.json", "w") as f:
        json.dump({k: {"date": v["date"].strftime('%Y-%m-%d'), "relationship": v.get("relationship", "other")} for k, v in birthdays.items()}, f)

def load_birthdays():
    global birthdays
    try:
        with open("birthdays.json", "r") as f:
            data = json.load(f)
            print("Loaded data from birthdays.json:", data)  # Debugging line
            birthdays = {}
            for name, details in data.items():
                print(f"Processing entry for {name}: {details}")  # Debugging line
                if isinstance(details, str):
                    # Old format with only the date
                    date_obj = datetime.strptime(details, '%Y-%m-%d')
                    birthdays[name] = {"date": date_obj, "relationship": "other"}
                elif isinstance(details, dict):
                    # New format with date and relationship
                    date_obj = datetime.strptime(details["date"], '%Y-%m-%d')
                    relationship = details.get("relationship", "other")
                    
                    # Correct any invalid relationships
                    if relationship == "TP":
                        relationship = "TP friend"
                    elif relationship == "friend":
                        relationship = "DA friend"
                    elif relationship not in ["family", "DA friend", "TP friend", "other"]:
                        print(f"Unexpected relationship '{relationship}' for {name}. Defaulting to 'other'.")
                        relationship = "other"
                    
                    birthdays[name] = {"date": date_obj, "relationship": relationship}
                else:
                    print(f"Skipping invalid entry for {name}: unexpected format")
            print("Final loaded birthdays:", birthdays)  # Debugging line
    except FileNotFoundError:
        print("birthdays.json file not found.")
        birthdays = {}

# Define the bot instance with intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Use this single instance for all commands and tasks
@bot.event
async def on_ready():
    load_birthdays()
    print(f"Logged in as {bot.user}")
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("The bot is ready!")
    else:
        print("Channel not found.")
    if not birthday_reminder.is_running():
        birthday_reminder.start()
        print("Birthday reminder task started.")  # Debugging log

# Keep your existing commands and tasks


@bot.command()
async def ping(ctx):
    """Check the bot's latency."""
    await ctx.send("Pong!")

@bot.command()
async def hello(ctx):
    """Say hello to the bot."""
    await ctx.send("Hello there!")

@bot.command()
async def help(ctx):
    """List all commands and their descriptions."""
    # Dynamically fetch all commands
    commands_list = bot.commands
    help_message = "**Available Commands:**\n"
    for command in commands_list:
        help_message += f"- `{bot.command_prefix}{command}`: {command.help}\n"
    await ctx.send(help_message)

@bot.command()
async def birthday_weather(ctx, location: str = "Cupertino"):
    """
    Fetch and display detailed weather data for a given location.
    Usage: !birthday_weather <location>
    If no location is provided, it defaults to Cupertino.
    """
    api_key =  # replace your API key here
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"

    # Map weather descriptions to emojis
    weather_emojis = {
        "clear sky": "☀️",
        "few clouds": "🌤️",
        "scattered clouds": "☁️",
        "broken clouds": "🌥️",
        "shower rain": "🌧️",
        "rain": "🌦️",
        "thunderstorm": "⛈️",
        "snow": "❄️",
        "mist": "🌫️",
    }

    try:
        response = requests.get(url).json()
        print(response)  # Debugging purposes

        if response["cod"] == 200:  # Check if the API call is successful
            # Extract data
            city = response["name"]
            weather = response["weather"][0]["description"]
            emoji = weather_emojis.get(weather, "🌍")  # Use default emoji if not mapped
            temperature = response["main"]["temp"]
            feels_like = response["main"]["feels_like"]
            humidity = response["main"]["humidity"]
            wind_speed = response["wind"]["speed"]
            pressure = response["main"]["pressure"]
            sunrise = datetime.fromtimestamp(response["sys"]["sunrise"]).strftime('%H:%M:%S')
            sunset = datetime.fromtimestamp(response["sys"]["sunset"]).strftime('%H:%M:%S')

            # Send the response as a message
            await ctx.send(
                f"**Weather in {city}:** {emoji}\n"
                f"- Description: {weather.capitalize()}\n"
                f"- Temperature: {temperature}°C\n"
                f"- Feels Like: {feels_like}°C\n"
                f"- Humidity: {humidity}%\n"
                f"- Wind Speed: {wind_speed} m/s\n"
                f"- Pressure: {pressure} hPa\n"
                f"- Sunrise: {sunrise}\n"
                f"- Sunset: {sunset}"
            )
        else:
            await ctx.send(f"Error: {response['message']}. Please check the location.")
    except Exception as e:
        await ctx.send("An error occurred while fetching the weather. Please try again later.")
        print(f"Error: {e}")

@bot.command()
async def add_birthday(ctx, friend_name: str, date: str, relationship: str = "other"):
    """
    Add a friend's birthday with an optional relationship.
    Usage: !add_birthday <friend_name> <YYYY-MM-DD> [relationship]
    """
    try:
        birthday_date = datetime.strptime(date, '%Y-%m-%d')
        birthdays[friend_name] = {"date": birthday_date, "relationship": relationship}
        save_birthdays()
        await ctx.send(f"🎉 Added {friend_name}'s birthday on {date} with relationship '{relationship}'!")
    except ValueError:
        await ctx.send("Invalid date format. Please use YYYY-MM-DD.")

# Command to remove a friend's birthday
@bot.command()
async def remove_birthday(ctx, friend_name: str):
    if friend_name in birthdays:
        del birthdays[friend_name]
        save_birthdays()
        await ctx.send(f"Birthday for {friend_name} has been removed.")
    else:
        await ctx.send(f"No birthday found for {friend_name} in the records.")

# Command to add relationship to multiple people
@bot.command()
async def add_relationship(ctx, relationship: str, *, names: str):
    """
    Assign a relationship category to multiple names.
    Usage: !add_relationship friend Name1, Name2, Name3
    """
    names_list = [name.strip() for name in names.split(",")]
    updated_names = []
    not_found_names = []

    for name in names_list:
        if name in birthdays:
            birthdays[name]["relationship"] = relationship
            updated_names.append(name)
        else:
            not_found_names.append(name)

    save_birthdays()  # Save the updated relationships to JSON

    # Send confirmation message
    response = ""
    if updated_names:
        response += f"Updated relationship to '{relationship}' for: {', '.join(updated_names)}.\n"
    if not_found_names:
        response += f"No birthday found for: {', '.join(not_found_names)}."

    await ctx.send(response)

@bot.command()
async def check_all_birthdays(ctx):
    if birthdays:
        # Sort birthdays by month and day
        sorted_birthdays = sorted(birthdays.items(), key=lambda x: (x[1]["date"].month, x[1]["date"].day))
        
        # Separate birthdays by relationship category with the correct categories
        categorized_birthdays = {"family": [], "DA friend": [], "TP friend": [], "other": []}
        
        for name, details in sorted_birthdays:
            date = details["date"]
            relationship = details.get("relationship", "other")  # Default to "other" if relationship is missing
            
            # Ensure the relationship is one of the initialized categories
            if relationship not in categorized_birthdays:
                relationship = "other"
            
            age_text = calculate_age(date)
            categorized_birthdays[relationship].append(f"**{name}**\nDate: {date.strftime('%Y-%m-%d')}\n{age_text}")

        # Define colors for each relationship type
        colors = {
            "family": discord.Color.red(),
            "DA friend": discord.Color.blue(),
            "TP friend": discord.Color.green(),
            "other": discord.Color.purple()
        }

        # Send a separate embed for each relationship category
        for category, entries in categorized_birthdays.items():
            if entries:
                embed = discord.Embed(
                    title=f"{category.capitalize()} Birthdays",
                    description="\n\n".join(entries),
                    color=colors[category]
                )
                await ctx.send(embed=embed)
    else:
        await ctx.send("No birthdays stored.")


# Helper function to calculate current and incoming age
def calculate_age(birth_date):
    today = datetime.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        return f"current age: {age - 1}, incoming age: {age}"
    else:
        return f"current age: {age}, incoming age: {age + 1}"

# Scheduled task to send reminders 2 weeks before birthdays
@tasks.loop(hours=24)  # Runs every 24 hours
async def birthday_reminder():
    print("Running birthday reminder task...")  # Debugging log
    today = datetime.today()
    reminder_start = today
    reminder_end = today + timedelta(weeks=2)  # Set the range for the next 2 weeks

    print(f"Today's date: {today.strftime('%Y-%m-%d')}")  # Debug log
    print(f"Checking birthdays between {reminder_start.strftime('%Y-%m-%d')} and {reminder_end.strftime('%Y-%m-%d')}")  # Debug log

    upcoming_birthdays = []

    for name, details in birthdays.items():
        birthday_date = details["date"]
        
        # Check if the birthday falls within the 2-week range (ignore the year)
        birthday_this_year = birthday_date.replace(year=today.year)
        if reminder_start <= birthday_this_year <= reminder_end:
            age = today.year - birthday_date.year
            upcoming_birthdays.append(f"{name} (Turning {age})")
            print(f"Upcoming birthday found: {name}")  # Debug log

    if upcoming_birthdays:
        # Send a message to the server channel
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await channel.send(f"🎉 Reminder: Upcoming birthdays in the next 2 weeks:\n" + "\n".join(upcoming_birthdays))
            print("Sent reminder to server channel.")  # Debug log

        # Optionally, send a combined DM to a specific user
        user = await bot.fetch_user(1107519870180012135)  # Replace with your numeric user ID
        if user:
            try:
                await user.send(f"🎉 Reminder: Upcoming birthdays in the next 2 weeks:\n" + "\n".join(upcoming_birthdays))
                print(f"Sent DM reminder to {user}.")  # Debug log
            except discord.Forbidden:
                print(f"Could not send DM to {user}.")  # Debug log
    else:
        print("No birthdays match the reminder date range.")  # Debug log



@bot.command()
async def debug_reminder(ctx):
    today = datetime.today()
    reminder_date = today + timedelta(weeks=2)
    await ctx.send(f"Today's date: {today.strftime('%Y-%m-%d')}")
    await ctx.send(f"Reminder date: {reminder_date.strftime('%Y-%m-%d')}")
    for name, details in birthdays.items():
        birthday_date = details["date"]
        await ctx.send(f"Checking {name}'s birthday: {birthday_date.strftime('%Y-%m-%d')}")
        if birthday_date.month == reminder_date.month and birthday_date.day == reminder_date.day:
            await ctx.send(f"Match found: {name}'s birthday is in 2 weeks!")




@bot.command()
async def add_test_birthday(ctx):
    """
    Add a test birthday for debugging purposes.
    """
    test_date = (datetime.today() + timedelta(weeks=2)).strftime('%Y-%m-%d')
    birthdays["Test User"] = {"date": datetime.strptime(test_date, '%Y-%m-%d'), "relationship": "friend"}
    save_birthdays()
    await ctx.send(f"Test birthday added for Test User on {test_date}.")

@bot.command()
async def test_channel(ctx):
    """
    Test if the bot can send messages to the designated channel.
    """
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("Testing channel permissions: ✅ Bot can send messages.")
        await ctx.send("Test message sent to the designated channel.")
    else:
        await ctx.send("Bot cannot access the specified channel.")

@bot.command()
async def check_birthday(ctx, name: str):
    """
    Check the stored birthday for a specific name.
    """
    if name in birthdays:
        details = birthdays[name]
        await ctx.send(
            f"**{name}** - Date: {details['date'].strftime('%Y-%m-%d')} "
            f"({details['relationship'].capitalize()})"
        )
    else:
        await ctx.send(f"No birthday found for {name}.")

@bot.command()
async def check_birthdays_by_month(ctx):
    if birthdays:
        # Sort birthdays by month and day
        sorted_birthdays = sorted(birthdays.items(), key=lambda x: (x[1]["date"].month, x[1]["date"].day))
        
        # Create a dictionary to hold birthdays by month
        month_birthdays = {month: [] for month in range(1, 13)}  # Initialize dictionary for each month

        for name, details in sorted_birthdays:
            date = details["date"]
            month_name = date.strftime("%B")
            age_text = calculate_age(date)
            month_birthdays[date.month].append(f"**{name}**\nDate: {date.strftime('%Y-%m-%d')}\n{age_text}")

        # Create an embed for each month with birthdays
        for month in range(1, 13):
            if month_birthdays[month]:  # Only add non-empty months
                month_name = datetime(1900, month, 1).strftime('%B')  # Get the month name
                embed = discord.Embed(
                    title=f"{month_name} Birthdays",
                    description="\n\n".join(month_birthdays[month]),
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)
    else:
        await ctx.send("No birthdays stored.")

@bot.command()
async def test_dm(ctx, user: discord.Member, *, message: str):
    """
    Test sending a DM to a user.
    """
    try:
        await user.send(message)
        await ctx.send(f"✅ DM sent to {user.name}.")
    except discord.Forbidden:
        await ctx.send(f"❌ Could not send a DM to {user.name}. They may have DMs disabled.")

@bot.command()
async def test_message(ctx):
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("This is a test message to the server channel.")
    else:
        await ctx.send("Could not find the server channel.")
    
    try:
        await ctx.author.send("This is a test DM.")
    except discord.Forbidden:
        await ctx.send("Unable to send DM. The user might have DMs disabled.")

# Run the bot
TOKEN = DISCORD_TOKEN
bot.run(TOKEN)
