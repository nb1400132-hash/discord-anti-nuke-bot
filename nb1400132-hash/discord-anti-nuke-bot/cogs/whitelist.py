import discord
from discord import app_commands
from discord.ext import commands
from utils.checks import is_owner_only
from utils.helpers import get_user_from_string

class Whitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='whitelist', description='Whitelist a user from anti-nuke punishments')
    @app_commands.describe(
        user='User mention, ID, or username to whitelist'
    )
    @is_owner_only()
    async def whitelist(self, interaction: discord.Interaction, user: discord.Member):
        if user.id == interaction.guild.owner_id:
            embed = discord.Embed(
                title="ℹ️ Already Immune",
                description="The server owner is already immune to all punishments.",
                color=0xffaa00
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if await self.bot.db.is_whitelisted(interaction.guild.id, user.id):
            embed = discord.Embed(
                title="ℹ️ Already Whitelisted",
                description=f"{user.mention} is already whitelisted.",
                color=0xffaa00
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await self.bot.db.add_whitelist(interaction.guild.id, user.id)
        
        embed = discord.Embed(
            title="✅ User Whitelisted",
            description=f"{user.mention} has been whitelisted and is now immune to anti-nuke punishments.",
            color=0x00ff00
        )
        embed.add_field(name="User", value=f"{user.mention}\n`{user.id}`", inline=False)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Whitelisted by {interaction.user}")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Whitelist(bot))
