import discord
from discord import app_commands
from discord.ext import commands
import json
import time
from utils.checks import is_owner_or_admin

class SaveServerSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_saves = {}
    
    @app_commands.command(name='saveserversettings', description='Save server backup (channels, roles, emojis, settings)')
    @is_owner_or_admin()
    async def saveserversettings(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        has_existing = await self.bot.db.has_server_backup(guild.id)
        
        if has_existing:
            if interaction.user.id in self.pending_saves and self.pending_saves[interaction.user.id] == guild.id:
                await self.perform_save(interaction)
                return
            
            self.pending_saves[interaction.user.id] = guild.id
            
            embed = discord.Embed(
                title="⚠️ Existing Save Found",
                description="You have an existing save for this server. If you save again, it will **overwrite** the previous backup.",
                color=0xffaa00
            )
            embed.add_field(
                name="⚠️ Warning",
                value="Are you sure you want to save? This will **overwrite your existing backup**.",
                inline=False
            )
            embed.add_field(
                name="To Confirm",
                value="Run `/saveserversettings` again to confirm and overwrite.",
                inline=False
            )
            embed.set_footer(text=f"Requested by {interaction.user}")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await self.perform_save(interaction)
    
    async def perform_save(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        if interaction.user.id in self.pending_saves:
            del self.pending_saves[interaction.user.id]
        
        await interaction.response.defer()
        
        backup_data = {
            'guild_id': guild.id,
            'guild_name': guild.name,
            'vanity_url': guild.vanity_url_code if guild.vanity_url_code else None,
            'icon_url': str(guild.icon.url) if guild.icon else None,
            'banner_url': str(guild.banner.url) if guild.banner else None,
            'description': guild.description,
            'channels': [],
            'roles': [],
            'emojis': []
        }
        
        for channel in guild.channels:
            channel_data = {
                'id': channel.id,
                'name': channel.name,
                'type': str(channel.type),
                'position': channel.position,
                'category_id': channel.category.id if channel.category else None,
                'overwrites': {}
            }
            
            if isinstance(channel, discord.TextChannel):
                channel_data['topic'] = channel.topic
                channel_data['slowmode_delay'] = channel.slowmode_delay
                channel_data['nsfw'] = channel.nsfw
            elif isinstance(channel, discord.VoiceChannel):
                channel_data['bitrate'] = channel.bitrate
                channel_data['user_limit'] = channel.user_limit
            
            for target, overwrite in channel.overwrites.items():
                key = f"role_{target.id}" if isinstance(target, discord.Role) else f"member_{target.id}"
                channel_data['overwrites'][key] = {
                    'allow': overwrite.pair()[0].value,
                    'deny': overwrite.pair()[1].value
                }
            
            backup_data['channels'].append(channel_data)
        
        for role in guild.roles:
            if role != guild.default_role:
                role_data = {
                    'id': role.id,
                    'name': role.name,
                    'color': role.color.value,
                    'permissions': role.permissions.value,
                    'position': role.position,
                    'hoist': role.hoist,
                    'mentionable': role.mentionable
                }
                backup_data['roles'].append(role_data)
        
        for emoji in guild.emojis:
            emoji_data = {
                'id': emoji.id,
                'name': emoji.name,
                'animated': emoji.animated,
                'url': str(emoji.url)
            }
            backup_data['emojis'].append(emoji_data)
        
        backup_json = json.dumps(backup_data)
        timestamp = int(time.time())
        
        await self.bot.db.save_server_backup(guild.id, backup_json, timestamp)
        
        embed = discord.Embed(
            title="✅ Server Backup Saved",
            description="Successfully saved server backup!",
            color=0x00ff00
        )
        embed.add_field(name="Channels Saved", value=str(len(backup_data['channels'])), inline=True)
        embed.add_field(name="Roles Saved", value=str(len(backup_data['roles'])), inline=True)
        embed.add_field(name="Emojis Saved", value=str(len(backup_data['emojis'])), inline=True)
        embed.add_field(name="Timestamp", value=f"<t:{timestamp}:F>", inline=False)
        embed.set_footer(text=f"Saved by {interaction.user}")
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SaveServerSettings(bot))
