import os
import discord
from discord.ext import commands
from Music import music
from dotenv import load_dotenv
load_dotenv()
client_id=os.environ.get("CLIENT_ID")
intents=discord.Intents.default()
intents.members=True
bot=commands.Bot("!",intents=intents)
@bot.event
async def on_ready():
    print("Ready")
async def setup():
    await bot.wait_until_ready()
    bot.add_cog(music(bot))
bot.loop.create_task(setup())
bot.run(client_id)
    