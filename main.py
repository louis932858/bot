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

GUILD_ID = 1470487831398056022

# =========================
# DATA
# =========================
aktive_dienste = {}
dienstzeiten = {}
original_names = {}

# =========================
# HELPERS
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


def get_active(guild):
    if not aktive_dienste:
        return "❌ Niemand im Dienst"

    text = ""
    for uid in aktive_dienste:
        member = guild.get_member(uid)
        if member:
            text += f"• {member.display_name}\n"

    return text


# =========================
# PANEL VIEW (BUTTON IDS)
# =========================
class ShiftPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # 🟢 BUTTON ON DUTY
    @discord.ui.button(
        label="Im Dienst",
        style=discord.ButtonStyle.success,
        emoji="🟢",
        custom_id="shift:on"
    )
    async def on_duty(self, interaction: discord.Interaction, button: discord.ui.Button):

        ok = await start_dienst(interaction.user)

        if not ok:
            await interaction.response.send_message("❌ Schon im Dienst!", ephemeral=True)
            return

        await self.update_panel(interaction)

        await interaction.response.send_message("🟢 Im Dienst!", ephemeral=True)

    # 🔴 BUTTON OFF DUTY
    @discord.ui.button(
        label="Aus Dienst",
        style=discord.ButtonStyle.danger,
        emoji="🔴",
        custom_id="shift:off"
    )
    async def off_duty(self, interaction: discord.Interaction, button: discord.ui.Button):

        dauer = await stop_dienst(interaction.user)

        if dauer is None:
            await interaction.response.send_message("❌ Nicht im Dienst!", ephemeral=True)
            return

        await self.update_panel(interaction)

        await interaction.response.send_message(
            f"🔴 Off Duty | ⏱️ {int(dauer // 60)} Min",
            ephemeral=True
        )

    # 🔄 LIVE UPDATE PANEL
    async def update_panel(self, interaction):

        embed = interaction.message.embeds[0]

        embed.set_field_at(
            0,
            name="🟢 Im Dienst",
            value=get_active(interaction.guild),
            inline=False
        )

        await interaction.message.edit(embed=embed, view=self)


# =========================
# PANEL COMMAND
# =========================
@bot.tree.command(name="panel", description="Shift Panel senden")
@app_commands.checks.has_permissions(administrator=True)
async def panel(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🛡️ Shift System",
        description="Nutze die Buttons um deinen Dienst zu steuern",
        color=0x2b2d31
    )

    embed.add_field(
        name="🟢 Im Dienst",
        value=get_active(interaction.guild),
        inline=False
    )

    await interaction.channel.send(embed=embed, view=ShiftPanel())
    await interaction.response.send_message("✅ Panel erstellt", ephemeral=True)


# =========================
# READY (IMPORTANT FOR BUTTON IDS)
# =========================
@bot.event
async def on_ready():
    print(f"Bot online {bot.user}")

    await bot.tree.sync()

    # 🔥 WICHTIG: Buttons bleiben nach Restart aktiv
    bot.add_view(ShiftPanel())


# =========================
# START
# =========================
bot.run(os.getenv("TOKEN"))
