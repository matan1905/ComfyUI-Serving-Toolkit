import discord
from discord.ext import commands


intents = discord.Intents.default()
intents.message_content = True
discord_client = commands.Bot(command_prefix='!', intents=intents)




# Event handler for when the bot is ready
@discord_client.event
async def on_ready():
    print(f'Logged in as {discord_client.user.name}. Ready to take requests!')

