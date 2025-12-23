import discord
from discord import app_commands
from discord.ext import commands
from utils.checks import is_owner_only

class AddAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name='addadmin', description='Add an admin who can modify anti-nuke settings')
    @app_commands.describe(
        user='User mention, ID, or username to add as admin'
    )
    @is_owner_only()
    async def addadmin(self, interaction: discord.Interaction, user: discord.Member):
        if user.id == interaction.guild.owner_id:
            embed = discord.Embed(
                title="ℹ️ Already Admin",
                description="The server owner already has full admin permissions.",
                color=0xffaa00
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if await self.bot.db.is_admin(interaction.guild.id, user.id):
            embed = discord.Embed(
                title="ℹ️ Already Admin",
                description=f"{user.mention} is already an admin.",
                color=0xffaa00
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await self.bot.db.add_admin(interaction.guild.id, user.id)
        
        embed = discord.Embed(
            title="✅ Admin Added",
            description=f"{user.mention} has been added as an admin and can now modify anti-nuke settings.",
            color=0x00ff00
        )
        embed.add_field(name="User", value=f"{user.mention}\n`{user.id}`", inline=False)
        embed.add_field(
            name="Permissions",
            value="• Set limits\n• Set timeframes\n• Set punishments\n• View configurations",
            inline=False
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Added by {interaction.user}")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(AddAdmin(bot))
