import discord
from discord import app_commands
from discord.ext import commands
from ..utils.embeds import create_help_embed

class HelpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="List all available commands and how to use them")
    async def help_command(self, interaction: discord.Interaction):
        help_embed = create_help_embed()
        await interaction.response.send_message(embed=help_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCommands(bot))
