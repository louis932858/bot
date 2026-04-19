import discord
from discord.ext import commands
from discord import app_commands
import datetime
import os

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

dienstzeiten = {}
aktive_dienste = {}

# 📅 Wochenplan
wochenplan = {
    "Montag": [],
    "Dienstag": [],
    "Mittwoch": [],
    "Donnerstag": [],
    "Freitag": [],
    "Samstag": [],
    "Sonntag": []
}

# 🔄 START
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Online: {bot.user}")

# 🟢 DIENST AN
@bot.tree.command(name="dienston")
async def dienston(interaction: discord.Interaction):
    user = interaction.user

    if user.id in aktive_dienste:
        await interaction.response.send_message("❌ Schon im Dienst!", ephemeral=True)
        return

    aktive_dienste[user.id] = datetime.datetime.now()

    try:
        await user.edit(nick=f"🟢 | {user.name}")
    except:
        pass

    await interaction.response.send_message("🟢 Dienst gestartet!")

# 🔴 DIENST AUS
@bot.tree.command(name="dienstoff")
async def dienstoff(interaction: discord.Interaction):
    user = interaction.user

    if user.id not in aktive_dienste:
        await interaction.response.send_message("❌ Nicht im Dienst!", ephemeral=True)
        return

    start = aktive_dienste.pop(user.id)
    dauer = (datetime.datetime.now() - start).total_seconds()

    dienstzeiten[user.id] = dienstzeiten.get(user.id, 0) + dauer

    try:
        await user.edit(nick=f"🔴 | {user.name}")
    except:
        pass

    await interaction.response.send_message("🔴 Dienst beendet!")

# 📅 SCHICHT ERSTELLEN (WOCHENTAG)
@bot.tree.command(name="schicht")
@app_commands.describe(
    tag="Wochentag (Montag-Sonntag)",
    user="User",
    zeit="Zeit (z.B. 18:00-22:00)"
)
async def schicht(interaction: discord.Interaction, tag: str, user: discord.Member, zeit: str):

    tag = tag.capitalize()

    if tag not in wochenplan:
        await interaction.response.send_message("❌ Ungültiger Wochentag!", ephemeral=True)
        return

    wochenplan[tag].append({
        "user": user.id,
        "zeit": zeit
    })

    await interaction.response.send_message(
        f"📅 Schicht erstellt:\n👤 {user.mention}\n📆 {tag}\n⏰ {zeit}"
    )

# 📋 WOCHENPLAN ANZEIGEN
@bot.tree.command(name="wochenplan")
async def wochenplan_show(interaction: discord.Interaction):

    text = "📅 **Wochenplan (Mo–So)**\n\n"

    for tag, schichten in wochenplan.items():
        text += f"📆 **{tag}**\n"

        if not schichten:
            text += "  - Keine Schichten\n\n"
            continue

        for s in schichten:
            user = await bot.fetch_user(s["user"])
            text += f"  👤 {user.name} | ⏰ {s['zeit']}\n"

        text += "\n"

    await interaction.response.send_message(text)

# ❌ PLAN LÖSCHEN
@bot.tree.command(name="wochenplan_reset")
async def reset(interaction: discord.Interaction):
    for k in wochenplan:
        wochenplan[k] = []

    await interaction.response.send_message("🗑️ Wochenplan zurückgesetzt!")

# 🔑 START
bot.run(os.getenv("TOKEN"))
