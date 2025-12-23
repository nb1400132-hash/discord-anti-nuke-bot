import discord
from discord import app_commands
from discord.ext import commands
from utils.checks import is_owner_only

class Unwhitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='unwhitelist', description='Remove a user from the whitelist')
    @app_commands.describe(
        user='User mention, ID, or username to remove from whitelist'
    )
    @is_owner_only()
    async def unwhitelist(self, interaction: discord.Interaction, user: discord.Member):
        if not await self.bot.db.is_whitelisted(interaction.guild.id, user.id):
            embed = discord.Embed(
                title="ℹ️ Not Whitelisted",
                description=f"{user.mention} is not currently whitelisted.",
                color=0xffaa00
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await self.bot.db.remove_whitelist(interaction.guild.id, user.id)
        
        embed = discord.Embed(
            title="✅ User Removed from Whitelist",
            description=f"{user.mention} has been removed from the whitelist and can now be punished by anti-nuke.",
            color=0x00ff00
        )
        embed.add_field(name="User", value=f"{user.mention}\n`{user.id}`", inline=False)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Removed by {interaction.user}")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Unwhitelist(bot))
