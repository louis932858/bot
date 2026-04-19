import discord
from discord.ext import commands
import os
import config
import time
import threading
import dashboard

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

warnings = {}
spam = {}

# Dashboard starten
threading.Thread(target=dashboard.run, daemon=True).start()


@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user}")


async def log(guild, msg):
    channel = discord.utils.get(guild.text_channels, name=config.LOG_CHANNEL)
    if channel:
        await channel.send(msg)


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = message.author.id
    gid = message.guild.id
    now = time.time()

    # ---- SPAM ----
    spam.setdefault(uid, [])
    spam[uid].append(now)
    spam[uid] = [t for t in spam[uid] if now - t < 5]

    if len(spam[uid]) > 5:
        await message.delete()
        await message.channel.send(f"🚫 Spam: {message.author.mention}")

        if message.author.voice:
            await message.author.move_to(None)
        return

    # ---- BAD WORDS ----
    if any(w in message.content.lower() for w in config.BAD_WORDS):

        warnings.setdefault(gid, {})
        warnings[gid].setdefault(uid, 0)
        warnings[gid][uid] += 1

        warn = warnings[gid][uid]

        await message.delete()

        await message.channel.send(
            f"⚠️ {message.author.mention} Warnung {warn}/{config.MAX_WARNINGS}"
        )

        await log(message.guild, f"Warn: {message.author} ({warn})")

        # Voice Kick
        if message.author.voice:
            await message.author.move_to(None)

        # Kick
        if warn >= config.MAX_WARNINGS:
            await message.author.kick(reason="Too many warnings")
            await log(message.guild, f"KICK: {message.author}")

        return

    await bot.process_commands(message)


@bot.command()
async def kick(ctx, member: discord.Member):
    await member.kick()
    await ctx.send(f"👢 {member} gekickt")

@bot.command()
async def ban(ctx, member: discord.Member):
    await member.ban()
    await ctx.send(f"🔨 {member} gebannt")


bot.run(os.getenv("TOKEN"))
