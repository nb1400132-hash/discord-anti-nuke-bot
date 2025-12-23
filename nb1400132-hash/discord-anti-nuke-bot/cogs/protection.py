import discord
from discord.ext import commands, tasks
import time
import asyncio
import json
from datetime import timedelta
from typing import Dict, Optional

DANGEROUS_PERMISSIONS = [
    discord.Permissions.administrator,
    discord.Permissions.kick_members,
    discord.Permissions.ban_members,
    discord.Permissions.manage_guild,
    discord.Permissions.manage_roles,
    discord.Permissions.manage_channels,
    discord.Permissions.manage_webhooks,
    discord.Permissions.mention_everyone
]

class Protection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_cache: Dict[int, Dict] = {}
        self.role_cache: Dict[int, Dict] = {}
        self.server_cache: Dict[int, Dict] = {}
        self.cache_updater.start()
    
    def cog_unload(self):
        self.cache_updater.cancel()
    
    @tasks.loop(minutes=5)
    async def cache_updater(self):
        for guild in self.bot.guilds:
            await self.cache_guild_state(guild)
    
    @cache_updater.before_loop
    async def before_cache_updater(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            await self.cache_guild_state(guild)
    
    async def cache_guild_state(self, guild: discord.Guild):
        if guild.id not in self.channel_cache:
            self.channel_cache[guild.id] = {}
        if guild.id not in self.role_cache:
            self.role_cache[guild.id] = {}
        if guild.id not in self.server_cache:
            self.server_cache[guild.id] = {}
        
        for channel in guild.channels:
            self.channel_cache[guild.id][channel.id] = await self.serialize_channel(channel)
        
        for role in guild.roles:
            if role != guild.default_role:
                self.role_cache[guild.id][role.id] = await self.serialize_role(role)
        
        self.server_cache[guild.id] = {
            'name': guild.name,
            'vanity_url': guild.vanity_url_code if guild.vanity_url_code else None,
            'icon': str(guild.icon.url) if guild.icon else None,
            'banner': str(guild.banner.url) if guild.banner else None,
            'description': guild.description
        }
    
    async def serialize_channel(self, channel):
        data = {
            'id': channel.id,
            'name': channel.name,
            'type': str(channel.type),
            'position': channel.position,
            'category_id': channel.category.id if channel.category else None,
            'overwrites': {}
        }
        
        if isinstance(channel, discord.TextChannel):
            data['topic'] = channel.topic
            data['slowmode_delay'] = channel.slowmode_delay
            data['nsfw'] = channel.nsfw
        elif isinstance(channel, discord.VoiceChannel):
            data['bitrate'] = channel.bitrate
            data['user_limit'] = channel.user_limit
        
        for target, overwrite in channel.overwrites.items():
            key = f"role_{target.id}" if isinstance(target, discord.Role) else f"member_{target.id}"
            data['overwrites'][key] = {
                'allow': overwrite.pair()[0].value,
                'deny': overwrite.pair()[1].value
            }
        
        return data
    
    async def serialize_role(self, role: discord.Role):
        return {
            'id': role.id,
            'name': role.name,
            'color': role.color.value,
            'permissions': role.permissions.value,
            'position': role.position,
            'hoist': role.hoist,
            'mentionable': role.mentionable
        }
    
    async def recreate_channel(self, guild: discord.Guild, channel_data: dict):
        try:
            category = guild.get_channel(channel_data['category_id']) if channel_data['category_id'] else None
            
            overwrites = {}
            for key, perms in channel_data['overwrites'].items():
                if key.startswith('role_'):
                    role_id = int(key.split('_')[1])
                    role = guild.get_role(role_id)
                    if role:
                        overwrites[role] = discord.PermissionOverwrite.from_pair(
                            discord.Permissions(perms['allow']),
                            discord.Permissions(perms['deny'])
                        )
                elif key.startswith('member_'):
                    member_id = int(key.split('_')[1])
                    member = guild.get_member(member_id)
                    if member:
                        overwrites[member] = discord.PermissionOverwrite.from_pair(
                            discord.Permissions(perms['allow']),
                            discord.Permissions(perms['deny'])
                        )
            
            if 'text' in channel_data['type']:
                new_channel = await guild.create_text_channel(
                    name=channel_data['name'],
                    category=category,
                    position=channel_data['position'],
                    topic=channel_data.get('topic'),
                    slowmode_delay=channel_data.get('slowmode_delay', 0),
                    nsfw=channel_data.get('nsfw', False),
                    overwrites=overwrites,
                    reason="Anti-Nuke: Restoring deleted channel"
                )
            elif 'voice' in channel_data['type']:
                new_channel = await guild.create_voice_channel(
                    name=channel_data['name'],
                    category=category,
                    position=channel_data['position'],
                    bitrate=channel_data.get('bitrate', 64000),
                    user_limit=channel_data.get('user_limit', 0),
                    overwrites=overwrites,
                    reason="Anti-Nuke: Restoring deleted channel"
                )
            elif 'category' in channel_data['type']:
                new_channel = await guild.create_category(
                    name=channel_data['name'],
                    position=channel_data['position'],
                    overwrites=overwrites,
                    reason="Anti-Nuke: Restoring deleted channel"
                )
            else:
                return None
            
            return new_channel
        except Exception as e:
            print(f"Failed to recreate channel: {e}")
            return None
    
    async def recreate_role(self, guild: discord.Guild, role_data: dict):
        try:
            new_role = await guild.create_role(
                name=role_data['name'],
                permissions=discord.Permissions(role_data['permissions']),
                color=discord.Color(role_data['color']),
                hoist=role_data['hoist'],
                mentionable=role_data['mentionable'],
                reason="Anti-Nuke: Restoring deleted role"
            )
            
            try:
                await new_role.edit(position=role_data['position'])
            except:
                pass
            
            return new_role
        except Exception as e:
            print(f"Failed to recreate role: {e}")
            return None
    
    def can_punish_user(self, guild: discord.Guild, user: discord.Member):
        bot_member = guild.get_member(self.bot.user.id)
        if not bot_member:
            return False
        
        if isinstance(user, discord.Member):
            return user.top_role < bot_member.top_role
        
        return False
    
    async def check_and_punish(self, guild, user, action: str, additional_info: str = "", target_data=None):
        if guild.owner_id == user.id:
            return False
        
        if await self.bot.db.is_whitelisted(guild.id, user.id):
            return False
        
        limit = await self.bot.db.get_limit(guild.id, action)
        if limit is None:
            return False
        
        timeframe = await self.bot.db.get_timeframe(guild.id, action)
        current_time = int(time.time())
        since_time = current_time - timeframe
        
        await self.bot.db.log_action(guild.id, user.id, action, current_time)
        
        action_count = await self.bot.db.get_recent_actions(guild.id, user.id, action, since_time)
        
        if action_count > limit:
            can_punish = self.can_punish_user(guild, user)
            
            if can_punish:
                punishment = await self.bot.db.get_punishment(guild.id, action)
                await self.execute_punishment(guild, user, punishment, action, additional_info)
            else:
                await self.send_log(
                    guild,
                    f"⚠️ Cannot punish {user.mention} (higher role than bot)",
                    user,
                    action.replace('_', ' ').title(),
                    f"User exceeded limit but has higher role. {additional_info}"
                )
            
            await self.revert_action(guild, action, target_data, user)
            return True
        
        return False
    
    async def revert_action(self, guild: discord.Guild, action: str, target_data, user):
        try:
            if action == 'deleting_channels' and target_data:
                channel_id = target_data.get('channel_id')
                if channel_id and guild.id in self.channel_cache and channel_id in self.channel_cache[guild.id]:
                    channel_data = self.channel_cache[guild.id][channel_id]
                    await self.recreate_channel(guild, channel_data)
                    await self.send_revert_log(guild, "Recreated deleted channel", channel_data['name'], user)
            
            elif action == 'creating_channels' and target_data:
                channel = target_data.get('channel')
                if channel:
                    await channel.delete(reason="Anti-Nuke: Unauthorized channel creation")
                    await self.send_revert_log(guild, "Deleted unauthorized channel", channel.name, user)
            
            elif action == 'deleting_roles' and target_data:
                role_id = target_data.get('role_id')
                if role_id and guild.id in self.role_cache and role_id in self.role_cache[guild.id]:
                    role_data = self.role_cache[guild.id][role_id]
                    await self.recreate_role(guild, role_data)
                    await self.send_revert_log(guild, "Recreated deleted role", role_data['name'], user)
            
            elif action == 'creating_roles' and target_data:
                role = target_data.get('role')
                if role:
                    await role.delete(reason="Anti-Nuke: Unauthorized role creation")
                    await self.send_revert_log(guild, "Deleted unauthorized role", role.name, user)
            
            elif action == 'banning_members' and target_data:
                banned_user = target_data.get('banned_user')
                if banned_user:
                    try:
                        await guild.unban(banned_user, reason="Anti-Nuke: Reverting unauthorized ban")
                        await self.send_revert_log(guild, "Unbanned user", str(banned_user), user)
                    except:
                        pass
            
            elif action == 'kicking_members' and target_data:
                kicked_user_id = target_data.get('kicked_user_id')
                if kicked_user_id:
                    await self.send_revert_log(guild, "Member was kicked (cannot reinvite)", f"User ID: {kicked_user_id}", user)
            
            elif action == 'updating_server' and target_data:
                old_name = target_data.get('old_name')
                old_vanity = target_data.get('old_vanity')
                
                if old_name and old_name != guild.name:
                    try:
                        await guild.edit(name=old_name, reason="Anti-Nuke: Reverting server name change")
                        await self.send_revert_log(guild, "Reverted server name", old_name, user)
                    except:
                        pass
                
                if old_vanity is not None and old_vanity != guild.vanity_url_code:
                    try:
                        await guild.edit(vanity_code=old_vanity if old_vanity else None, reason="Anti-Nuke: Reverting vanity URL change")
                        await self.send_revert_log(guild, "Reverted vanity URL", old_vanity or "None", user)
                    except:
                        pass
        
        except Exception as e:
            print(f"Failed to revert action {action}: {e}")
    
    async def send_revert_log(self, guild: discord.Guild, action: str, target: str, user):
        embed = discord.Embed(
            title="🔄 Anti-Nuke Revert Action",
            description=f"**{action}**: {target}",
            color=0x00ffff,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Perpetrator", value=f"{user.mention}\n`{user.id}`", inline=True)
        embed.add_field(name="Status", value="✅ Reverted", inline=True)
        
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                try:
                    await channel.send(embed=embed)
                    break
                except:
                    continue
    
    async def execute_punishment(self, guild, user, punishment: str, action: str, additional_info: str):
        action_name = action.replace('_', ' ').title()
        reason = f"Anti-Nuke: Exceeded limit for {action_name}"
        if additional_info:
            reason += f" | {additional_info}"
        
        member = guild.get_member(user.id)
        if not member:
            return
        
        bot_member = guild.get_member(self.bot.user.id)
        if member.top_role >= bot_member.top_role:
            return
        
        try:
            if punishment == 'ban':
                await member.ban(reason=reason)
                log_msg = f"🔨 Banned {member.mention} for {action_name}"
            elif punishment == 'kick':
                await member.kick(reason=reason)
                log_msg = f"👢 Kicked {member.mention} for {action_name}"
            elif punishment == 'clear_roles':
                roles_to_remove = [role for role in member.roles if role != guild.default_role and role < bot_member.top_role]
                await member.remove_roles(*roles_to_remove, reason=reason)
                log_msg = f"🔓 Cleared roles for {member.mention} for {action_name}"
            elif punishment == 'timeout':
                await member.timeout(timedelta(days=1), reason=reason)
                log_msg = f"⏰ Timed out {member.mention} for {action_name}"
            elif punishment == 'warn':
                log_msg = f"⚠️ Warning for {member.mention} for {action_name}"
            else:
                return
            
            await self.send_log(guild, log_msg, member, action_name, reason)
        except Exception as e:
            print(f"Failed to execute punishment: {e}")
    
    async def send_log(self, guild, message: str, member, action: str, reason: str):
        embed = discord.Embed(
            title="🛡️ Anti-Nuke Action Taken",
            description=message,
            color=0xff0000,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="User", value=f"{member.mention}\n`{member.id}`", inline=True)
        embed.add_field(name="Action", value=action, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        if hasattr(member, 'display_avatar'):
            embed.set_thumbnail(url=member.display_avatar.url)
        
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                try:
                    await channel.send(embed=embed)
                    break
                except:
                    continue
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.cache_guild_state(guild)
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await asyncio.sleep(1)
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                target_data = {'banned_user': user}
                await self.check_and_punish(guild, entry.user, 'banning_members', f"Banned {user}", target_data)
                break
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await asyncio.sleep(1)
        async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id:
                target_data = {'kicked_user_id': member.id}
                await self.check_and_punish(member.guild, entry.user, 'kicking_members', f"Kicked {member}", target_data)
                break
    
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        await asyncio.sleep(1)
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
            if entry.target.id == channel.id:
                target_data = {'channel': channel}
                await self.check_and_punish(channel.guild, entry.user, 'creating_channels', f"Created #{channel.name}", target_data)
                break
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        channel_id = channel.id
        guild_id = channel.guild.id
        
        if guild_id in self.channel_cache:
            if channel_id not in self.channel_cache[guild_id]:
                self.channel_cache[guild_id][channel_id] = await self.serialize_channel(channel)
        
        await asyncio.sleep(1)
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            if entry.target.id == channel_id:
                target_data = {'channel_id': channel_id}
                await self.check_and_punish(channel.guild, entry.user, 'deleting_channels', f"Deleted #{channel.name}", target_data)
                break
    
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        await self.cache_guild_state(after.guild)
        
        await asyncio.sleep(1)
        async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
            if entry.target.id == after.id:
                await self.check_and_punish(after.guild, entry.user, 'editing_channels', f"Edited #{after.name}")
                break
    
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        await asyncio.sleep(1)
        async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
            if entry.target.id == role.id:
                target_data = {'role': role}
                await self.check_and_punish(role.guild, entry.user, 'creating_roles', f"Created @{role.name}", target_data)
                break
    
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        role_id = role.id
        guild_id = role.guild.id
        
        if guild_id in self.role_cache:
            if role_id not in self.role_cache[guild_id]:
                self.role_cache[guild_id][role_id] = await self.serialize_role(role)
        
        await asyncio.sleep(1)
        async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            if entry.target.id == role_id:
                target_data = {'role_id': role_id}
                await self.check_and_punish(role.guild, entry.user, 'deleting_roles', f"Deleted @{role.name}", target_data)
                break
    
    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        await self.cache_guild_state(after.guild)
        
        await asyncio.sleep(1)
        async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
            if entry.target.id == after.id:
                before_perms = before.permissions
                after_perms = after.permissions
                
                if not before_perms.administrator and after_perms.administrator:
                    await self.check_and_punish(after.guild, entry.user, 'giving_administrative_roles', f"Gave administrator to @{after.name}")
                
                dangerous_added = False
                for perm_value in DANGEROUS_PERMISSIONS:
                    before_has = before_perms.value & perm_value.value
                    after_has = after_perms.value & perm_value.value
                    if not before_has and after_has:
                        dangerous_added = True
                        break
                
                if dangerous_added:
                    await self.check_and_punish(after.guild, entry.user, 'giving_dangerous_permissions', f"Gave dangerous permissions to @{after.name}")
                else:
                    await self.check_and_punish(after.guild, entry.user, 'editing_roles', f"Edited @{after.name}")
                break
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles == after.roles:
            return
        
        added_roles = set(after.roles) - set(before.roles)
        
        for role in added_roles:
            if role.permissions.administrator:
                await asyncio.sleep(1)
                async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                    if entry.target.id == after.id:
                        await self.check_and_punish(after.guild, entry.user, 'giving_administrative_roles', f"Gave @{role.name} to {after.mention}")
                        break
                return
            
            has_dangerous = False
            for perm_value in DANGEROUS_PERMISSIONS:
                if role.permissions.value & perm_value.value:
                    has_dangerous = True
                    break
            
            if has_dangerous:
                await asyncio.sleep(1)
                async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                    if entry.target.id == after.id:
                        await self.check_and_punish(after.guild, entry.user, 'giving_dangerous_permissions', f"Gave @{role.name} to {after.mention}")
                        break
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            await asyncio.sleep(2)
            async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
                if entry.target.id == member.id:
                    await self.bot.db.set_bot_owner(member.guild.id, member.id, entry.user.id)
                    
                    target_data = {'bot': member}
                    was_punished = await self.check_and_punish(member.guild, entry.user, 'adding_bots', f"Added bot {member.mention}", target_data)
                    
                    if was_punished:
                        try:
                            await member.ban(reason="Anti-Nuke: Bot added by user who exceeded limit")
                        except:
                            pass
                    break
    
    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        if before.name != after.name or before.vanity_url_code != after.vanity_url_code:
            old_cached = self.server_cache.get(after.id, {})
            
            await asyncio.sleep(1)
            async for entry in after.audit_logs(limit=1, action=discord.AuditLogAction.guild_update):
                target_data = {
                    'old_name': before.name,
                    'old_vanity': before.vanity_url_code
                }
                await self.check_and_punish(after, entry.user, 'updating_server', f"Updated server settings", target_data)
                break
        
        await self.cache_guild_state(after)
    
    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        await asyncio.sleep(1)
        
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.webhook_create):
            target_data = {'webhook': entry.target}
            was_punished = await self.check_and_punish(channel.guild, entry.user, 'creating_webhooks', f"Created webhook in #{channel.name}", target_data)
            if was_punished:
                try:
                    webhook = entry.target
                    if webhook:
                        await webhook.delete(reason="Anti-Nuke: Unauthorized webhook creation")
                except:
                    pass
            break
        
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.webhook_delete):
            await self.check_and_punish(channel.guild, entry.user, 'deleting_webhooks', f"Deleted webhook")
            break
    
    @commands.Cog.listener()
    async def on_guild_integrations_update(self, guild):
        await asyncio.sleep(1)
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.integration_create):
            await self.check_and_punish(guild, entry.user, 'authorizing_applications', f"Authorized application")
            break

async def setup(bot):
    await bot.add_cog(Protection(bot))
