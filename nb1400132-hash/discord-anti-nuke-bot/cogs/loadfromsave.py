import discord
from discord import app_commands
from discord.ext import commands
import json
import asyncio
from utils.checks import is_owner_or_admin

class LoadFromSave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_loads = {}
    
    @app_commands.command(name='loadfromsave', description='Load server from backup (WARNING: Deletes all current channels first)')
    @is_owner_or_admin()
    async def loadfromsave(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        backup_result = await self.bot.db.get_server_backup(guild.id)
        
        if not backup_result:
            embed = discord.Embed(
                title="❌ No Backup Found",
                description="No backup exists for this server. Use `/saveserversettings` to create one first.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if interaction.user.id in self.pending_loads and self.pending_loads[interaction.user.id] == guild.id:
            await self.perform_load(interaction, backup_result)
            return
        
        self.pending_loads[interaction.user.id] = guild.id
        
        backup_data = json.loads(backup_result[0])
        timestamp = backup_result[1]
        
        embed = discord.Embed(
            title="⚠️ WARNING: Server Restore",
            description="**This will delete ALL current channels and restore from backup!**",
            color=0xff0000
        )
        embed.add_field(name="⚠️ DANGER", value="This action will:\n• Delete all current channels\n• Delete all current roles (except @everyone)\n• Recreate everything from backup", inline=False)
        embed.add_field(name="Backup Info", value=f"Saved: <t:{timestamp}:F>\nChannels: {len(backup_data['channels'])}\nRoles: {len(backup_data['roles'])}\nEmojis: {len(backup_data['emojis'])}", inline=False)
        embed.add_field(name="To Confirm", value="Run `/loadfromsave` again within 60 seconds to confirm.", inline=False)
        embed.set_footer(text=f"Requested by {interaction.user}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        await asyncio.sleep(60)
        if interaction.user.id in self.pending_loads and self.pending_loads[interaction.user.id] == guild.id:
            del self.pending_loads[interaction.user.id]
    
    async def perform_load(self, interaction: discord.Interaction, backup_result):
        guild = interaction.guild
        
        if interaction.user.id in self.pending_loads:
            del self.pending_loads[interaction.user.id]
        
        await interaction.response.defer()
        
        backup_json, timestamp = backup_result
        backup_data = json.loads(backup_json)
        
        if backup_data['guild_id'] != guild.id:
            embed = discord.Embed(
                title="❌ Backup Mismatch",
                description="This backup is for a different server!",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        status_embed = discord.Embed(
            title="🔄 Restoring Server...",
            description="Please wait while the server is restored from backup.",
            color=0xffaa00
        )
        status_msg = await interaction.followup.send(embed=status_embed)
        
        deleted_channels = 0
        for channel in guild.channels:
            try:
                await channel.delete(reason="Anti-Nuke: Preparing for server restore")
                deleted_channels += 1
            except:
                pass
        
        status_embed.add_field(name="Step 1", value=f"✅ Deleted {deleted_channels} channels", inline=False)
        await status_msg.edit(embed=status_embed)
        
        deleted_roles = 0
        for role in guild.roles:
            if role != guild.default_role and role.name != guild.me.name and role < guild.me.top_role:
                try:
                    await role.delete(reason="Anti-Nuke: Preparing for server restore")
                    deleted_roles += 1
                except:
                    pass
        
        status_embed.add_field(name="Step 2", value=f"✅ Deleted {deleted_roles} roles", inline=False)
        await status_msg.edit(embed=status_embed)
        
        if backup_data['guild_name'] != guild.name:
            try:
                await guild.edit(name=backup_data['guild_name'], reason="Anti-Nuke: Restoring server name")
            except:
                pass
        
        if backup_data['vanity_url'] and backup_data['vanity_url'] != guild.vanity_url_code:
            try:
                await guild.edit(vanity_code=backup_data['vanity_url'], reason="Anti-Nuke: Restoring vanity URL")
            except:
                pass
        
        status_embed.add_field(name="Step 3", value=f"✅ Restored server settings", inline=False)
        await status_msg.edit(embed=status_embed)
        
        role_mapping = {}
        sorted_roles = sorted(backup_data['roles'], key=lambda r: r['position'])
        
        for role_data in sorted_roles:
            try:
                new_role = await guild.create_role(
                    name=role_data['name'],
                    permissions=discord.Permissions(role_data['permissions']),
                    color=discord.Color(role_data['color']),
                    hoist=role_data['hoist'],
                    mentionable=role_data['mentionable'],
                    reason="Anti-Nuke: Restoring from backup"
                )
                role_mapping[role_data['id']] = new_role
            except Exception as e:
                print(f"Failed to create role: {e}")
        
        status_embed.add_field(name="Step 4", value=f"✅ Created {len(role_mapping)} roles", inline=False)
        await status_msg.edit(embed=status_embed)
        
        category_mapping = {}
        categories = [c for c in backup_data['channels'] if 'category' in c['type']]
        sorted_categories = sorted(categories, key=lambda c: c['position'])
        
        for category_data in sorted_categories:
            try:
                overwrites = {}
                for key, perms in category_data['overwrites'].items():
                    if key.startswith('role_'):
                        role_id = int(key.split('_')[1])
                        if role_id in role_mapping:
                            overwrites[role_mapping[role_id]] = discord.PermissionOverwrite.from_pair(
                                discord.Permissions(perms['allow']),
                                discord.Permissions(perms['deny'])
                            )
                
                new_category = await guild.create_category(
                    name=category_data['name'],
                    position=category_data['position'],
                    overwrites=overwrites,
                    reason="Anti-Nuke: Restoring from backup"
                )
                category_mapping[category_data['id']] = new_category
            except Exception as e:
                print(f"Failed to create category: {e}")
        
        status_embed.add_field(name="Step 5", value=f"✅ Created {len(category_mapping)} categories", inline=False)
        await status_msg.edit(embed=status_embed)
        
        regular_channels = [c for c in backup_data['channels'] if 'category' not in c['type']]
        sorted_channels = sorted(regular_channels, key=lambda c: c['position'])
        created_channels = 0
        
        for channel_data in sorted_channels:
            try:
                category = category_mapping.get(channel_data['category_id'])
                
                overwrites = {}
                for key, perms in channel_data['overwrites'].items():
                    if key.startswith('role_'):
                        role_id = int(key.split('_')[1])
                        if role_id in role_mapping:
                            overwrites[role_mapping[role_id]] = discord.PermissionOverwrite.from_pair(
                                discord.Permissions(perms['allow']),
                                discord.Permissions(perms['deny'])
                            )
                
                if 'text' in channel_data['type']:
                    await guild.create_text_channel(
                        name=channel_data['name'],
                        category=category,
                        position=channel_data['position'],
                        topic=channel_data.get('topic'),
                        slowmode_delay=channel_data.get('slowmode_delay', 0),
                        nsfw=channel_data.get('nsfw', False),
                        overwrites=overwrites,
                        reason="Anti-Nuke: Restoring from backup"
                    )
                    created_channels += 1
                elif 'voice' in channel_data['type']:
                    await guild.create_voice_channel(
                        name=channel_data['name'],
                        category=category,
                        position=channel_data['position'],
                        bitrate=channel_data.get('bitrate', 64000),
                        user_limit=channel_data.get('user_limit', 0),
                        overwrites=overwrites,
                        reason="Anti-Nuke: Restoring from backup"
                    )
                    created_channels += 1
            except Exception as e:
                print(f"Failed to create channel: {e}")
        
        status_embed.add_field(name="Step 6", value=f"✅ Created {created_channels} channels", inline=False)
        await status_msg.edit(embed=status_embed)
        
        final_embed = discord.Embed(
            title="✅ Server Restored Successfully",
            description="Server has been restored from backup!",
            color=0x00ff00
        )
        final_embed.add_field(name="Channels Restored", value=str(created_channels + len(category_mapping)), inline=True)
        final_embed.add_field(name="Roles Restored", value=str(len(role_mapping)), inline=True)
        final_embed.add_field(name="Backup Date", value=f"<t:{timestamp}:F>", inline=False)
        final_embed.set_footer(text=f"Restored by {interaction.user}")
        
        await status_msg.edit(embed=final_embed)

async def setup(bot):
    await bot.add_cog(LoadFromSave(bot))
