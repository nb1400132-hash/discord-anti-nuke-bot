import discord
from discord import app_commands

def is_owner_or_admin():
    async def predicate(interaction: discord.Interaction) -> bool:
        bot = interaction.client
        
        if interaction.guild.owner_id == interaction.user.id:
            return True
        
        if await bot.db.is_admin(interaction.guild.id, interaction.user.id):
            return True
        
        embed = discord.Embed(
            title="❌ Access Denied",
            description="Only the server owner or authorized admins can use this command.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False
    
    return app_commands.check(predicate)

def is_owner_only():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.guild.owner_id == interaction.user.id:
            return True
        
        embed = discord.Embed(
            title="❌ Access Denied",
            description="Only the server owner can use this command.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False
    
    return app_commands.check(predicate)
