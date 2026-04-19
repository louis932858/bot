import discord
from discord.ext import commands
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

BAD_WORDS = ["hurensohn", "idiot", "opfer"]

@bot.event
async def on_ready():
    print(f"Bot ist online als {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    text = message.content.lower()

    if any(word in text for word in BAD_WORDS):
        if message.author.voice:
            try:
                await message.author.move_to(None)  # Kick aus Voice
                await message.channel.send(f"🚫 {message.author.mention} wurde aus dem Voice gekickt (Beleidigung)")
            except:
                await message.channel.send("❌ Konnte User nicht kicken (fehlende Rechte?)")

    await bot.process_commands(message)

bot.run(os.getenv("TOKEN"))
