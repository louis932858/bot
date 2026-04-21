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

bot = commands.Bot(command_prefix="/", intents=intents)

# =========================
# SERVER ID
# =========================
GUILD_ID = 1470487831398056022

# =========================
# SPEICHER
# =========================
dienstzeiten = {}
aktive_dienste = {}
original_names = {}

# =========================
# HELPER
# =========================
def get_active_list(guild):
    if not aktive_dienste:
        return "❌ Niemand im Dienst"

    text = ""

    for uid in aktive_dienste:
        member = guild.get_member(uid)
        if member:
            text += f"🟢 {member.display_name}\n"

    return text


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


# =========================
# PANEL VIEW
# =========================
class DienstPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Im Dienst", style=discord.ButtonStyle.success, emoji="🟢")
    async def on(self, interaction: discord.Interaction, button: discord.ui.Button):

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

        await interaction.response.send_message("🟢 Du bist im Dienst", ephemeral=True)

    @discord.ui.button(label="Aus Dienst", style=discord.ButtonStyle.danger, emoji="🔴")
    async def off(self, interaction: discord.Interaction, button: discord.ui.Button):

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
# PANEL COMMAND (KEINE PERMISSIONS PROBLEME)
# =========================
@bot.tree.command(name="panel", description="Shift Panel senden")
async def panel(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🛡️ SHIFT SYSTEM",
        description="Drücke die Buttons um deinen Dienst zu steuern",
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
# LEADERBOARD
# =========================
@bot.tree.command(name="leaderboard", description="Zeigt die aktivsten User")
async def leaderboard(interaction: discord.Interaction):

    if not dienstzeiten:
        await interaction.response.send_message("📭 Keine Daten")
        return

    sorted_users = sorted(dienstzeiten.items(), key=lambda x: x[1], reverse=True)

    text = "🏆 **Leaderboard**\n\n"

    for i, (uid, sec) in enumerate(sorted_users[:10], start=1):
        user = await bot.fetch_user(uid)
        text += f"{i}. {user.name} - {round(sec/3600, 2)}h\n"

    await interaction.response.send_message(text)


# =========================
# READY
# =========================
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)

    await bot.tree.sync(guild=guild)

    bot.add_view(DienstPanel())  # wichtig für Buttons nach Restart

    print(f"✅ Bot online: {bot.user}")


# =========================
# START
# =========================
bot.run(os.getenv("TOKEN"))
