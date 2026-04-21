import discord
from discord.ext import commands
from discord import app_commands
import datetime
import os

# =========================
# INTENTS
# =========================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

GUILD_ID = 1470487831398056022

# =========================
# SPEICHER
# =========================
dienstzeiten = {}
aktive_dienste = {}
dienstplan = {}
original_names = {}

# =========================
# HELPER
# =========================
async def start_dienst(user):
    if user.id in aktive_dienste:
        return False

    aktive_dienste[user.id] = datetime.datetime.now()
    original_names[user.id] = user.display_name

    try:
        await user.edit(nick=f"[ON DUTY] {user.name}")
    except:
        pass

    return True


async def stop_dienst(user):
    if user.id not in aktive_dienste:
        return None

    start = aktive_dienste.pop(user.id)
    dauer = (datetime.datetime.now() - start).total_seconds()

    dienstzeiten[user.id] = dienstzeiten.get(user.id, 0) + dauer

    original = original_names.get(user.id)

    try:
        await user.edit(nick=original)
    except:
        pass

    return dauer


def get_active_list(guild):
    if not aktive_dienste:
        return "❌ Niemand im Dienst"

    text = ""
    for uid in aktive_dienste:
        member = guild.get_member(uid)
        if member:
            text += f"• {member.display_name}\n"

    return text if text else "❌ Niemand im Dienst"

# =========================
# PANEL
# =========================
class DienstPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Im Dienst", style=discord.ButtonStyle.success, emoji="🟢")
    async def dienst_an(self, interaction: discord.Interaction, button: discord.ui.Button):

        ok = await start_dienst(interaction.user)

        if not ok:
            await interaction.response.send_message("❌ Du bist schon im Dienst!", ephemeral=True)
            return

        embed = interaction.message.embeds[0]
        embed.set_field_at(
            0,
            name="🟢 Aktuell im Dienst",
            value=get_active_list(interaction.guild),
            inline=False
        )

        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message("🟢 Du bist jetzt im Dienst!", ephemeral=True)

    @discord.ui.button(label="Aus Dienst", style=discord.ButtonStyle.danger, emoji="🔴")
    async def dienst_aus(self, interaction: discord.Interaction, button: discord.ui.Button):

        dauer = await stop_dienst(interaction.user)

        if dauer is None:
            await interaction.response.send_message("❌ Du bist nicht im Dienst!", ephemeral=True)
            return

        embed = interaction.message.embeds[0]
        embed.set_field_at(
            0,
            name="🟢 Aktuell im Dienst",
            value=get_active_list(interaction.guild),
            inline=False
        )

        await interaction.message.edit(embed=embed, view=self)

        await interaction.response.send_message(
            f"🔴 Dienst beendet! ⏱️ {int(dauer // 60)} Minuten",
            ephemeral=True
        )

# =========================
# PANEL COMMAND
# =========================
@bot.tree.command(name="panel", description="Shift Panel senden")
@app_commands.checks.has_permissions(administrator=True)
async def panel(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🛡️ Dienst System",
        description="Nutze die Buttons um deinen Dienst zu steuern",
        color=0x2b2d31
    )

    embed.add_field(
        name="🟢 Aktuell im Dienst",
        value=get_active_list(interaction.guild),
        inline=False
    )

    await interaction.channel.send(embed=embed, view=DienstPanel())
    await interaction.response.send_message("✅ Panel erstellt", ephemeral=True)

# =========================
# COMMANDS
# =========================
@bot.tree.command(name="dienston")
async def dienston(interaction: discord.Interaction):
    ok = await start_dienst(interaction.user)

    if not ok:
        await interaction.response.send_message("❌ Du bist schon im Dienst!", ephemeral=True)
        return

    await interaction.response.send_message("🟢 Du bist jetzt im Dienst!")


@bot.tree.command(name="dienstoff")
async def dienstoff(interaction: discord.Interaction):
    dauer = await stop_dienst(interaction.user)

    if dauer is None:
        await interaction.response.send_message("❌ Du bist nicht im Dienst!", ephemeral=True)
        return

    await interaction.response.send_message(
        f"🔴 Dienst beendet! ⏱️ {int(dauer // 60)} Minuten"
    )

# =========================
# LEADERBOARD
# =========================
@bot.tree.command(name="leaderboard")
async def leaderboard(interaction: discord.Interaction):

    if not dienstzeiten:
        await interaction.response.send_message("📭 Keine Daten vorhanden.")
        return

    sorted_users = sorted(dienstzeiten.items(), key=lambda x: x[1], reverse=True)

    text = "🏆 **Leaderboard**\n\n"

    for i, (uid, sec) in enumerate(sorted_users[:10], start=1):
        user = await bot.fetch_user(uid)
        text += f"{i}. {user.name} - {round(sec/3600, 2)}h\n"

    await interaction.response.send_message(text)

# =========================
# DIENSTPLAN
# =========================
@bot.tree.command(name="schicht")
@app_commands.describe(tag="Montag-Sonntag", user="User", zeit="18:00-22:00")
async def schicht(interaction: discord.Interaction, tag: str, user: discord.Member, zeit: str):

    tag = tag.capitalize()
    wochen = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]

    if tag not in wochen:
        await interaction.response.send_message("❌ Ungültiger Tag!", ephemeral=True)
        return

    if tag not in dienstplan:
        dienstplan[tag] = []

    dienstplan[tag].append({"user": user.id, "zeit": zeit})

    await interaction.response.send_message(
        f"📅 Schicht erstellt:\n📆 {tag}\n👤 {user.mention}\n⏰ {zeit}"
    )

@bot.tree.command(name="dienstplan")
async def dienstplan_show(interaction: discord.Interaction):

    if not dienstplan:
        await interaction.response.send_message("📭 Kein Plan vorhanden.")
        return

    text = "📅 **Wochenplan**\n\n"

    tage = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]

    for tag in tage:
        text += f"📆 **{tag}**\n"

        if tag in dienstplan:
            for s in dienstplan[tag]:
                user = await bot.fetch_user(s["user"])
                text += f"👤 {user.name} | ⏰ {s['zeit']}\n"
        else:
            text += "Keine Schichten\n"

        text += "\n"

    await interaction.response.send_message(text)

@bot.tree.command(name="resetplan")
async def resetplan(interaction: discord.Interaction):
    dienstplan.clear()
    await interaction.response.send_message("🗑️ Plan gelöscht!")

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)

    await bot.tree.sync(guild=guild)
    bot.add_view(DienstPanel())

    print(f"✅ Bot online: {bot.user}")

# =========================
# START
# =========================
bot.run(os.getenv("TOKEN"))
