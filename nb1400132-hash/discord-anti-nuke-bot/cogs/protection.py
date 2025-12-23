import discord
from discord.ext import commands
import time
from datetime import timedelta

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
    
    async def check_and_punish(self, guild, user, action: str, additional_info: str = ""):
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
            punishment = await self.bot.db.get_punishment(guild.id, action)
            await self.execute_punishment(guild, user, punishment, action, additional_info)
            return True
        
        return False
    
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
    
    async def send_log(self, guild, message: str, member: discord.Member, action: str, reason: str):
        embed = discord.Embed(
            title="🛡️ Anti-Nuke Action Taken",
            description=message,
            color=0xff0000,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="User", value=f"{member.mention}\n`{member.id}`", inline=True)
        embed.add_field(name="Action", value=action, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                try:
                    await channel.send(embed=embed)
                    break
                except:
                    continue
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                await self.check_and_punish(guild, entry.user, 'banning_members', f"Banned {user}")
                break
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await asyncio.sleep(1)
        async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id:
                await self.check_and_punish(member.guild, entry.user, 'kicking_members', f"Kicked {member}")
                break
    
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
            if entry.target.id == channel.id:
                was_punished = await self.check_and_punish(channel.guild, entry.user, 'creating_channels', f"Created #{channel.name}")
                if was_punished:
                    try:
                        await channel.delete(reason="Anti-Nuke: Unauthorized channel creation")
                    except:
                        pass
                break
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            if entry.target.id == channel.id:
                await self.check_and_punish(channel.guild, entry.user, 'deleting_channels', f"Deleted #{channel.name}")
                break
    
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
            if entry.target.id == after.id:
                await self.check_and_punish(after.guild, entry.user, 'editing_channels', f"Edited #{after.name}")
                break
    
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
            if entry.target.id == role.id:
                was_punished = await self.check_and_punish(role.guild, entry.user, 'creating_roles', f"Created @{role.name}")
                if was_punished:
                    try:
                        await role.delete(reason="Anti-Nuke: Unauthorized role creation")
                    except:
                        pass
                break
    
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            if entry.target.id == role.id:
                await self.check_and_punish(role.guild, entry.user, 'deleting_roles', f"Deleted @{role.name}")
                break
    
    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
            if entry.target.id == after.id:
                before_perms = before.permissions
                after_perms = after.permissions
                
                if not before_perms.administrator and after_perms.administrator:
                    await self.check_and_punish(after.guild, entry.user, 'giving_administrative_roles', f"Gave administrator to @{after.name}")
                
                dangerous_added = False
                for perm in DANGEROUS_PERMISSIONS:
                    if not before_perms.is_superset(perm) and after_perms.is_superset(perm):
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
                async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                    if entry.target.id == after.id:
                        await self.check_and_punish(after.guild, entry.user, 'giving_administrative_roles', f"Gave @{role.name} to {after.mention}")
                        break
                return
            
            has_dangerous = False
            for perm in DANGEROUS_PERMISSIONS:
                if role.permissions.is_superset(perm):
                    has_dangerous = True
                    break
            
            if has_dangerous:
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
                    
                    was_punished = await self.check_and_punish(member.guild, entry.user, 'adding_bots', f"Added bot {member.mention}")
                    
                    if was_punished:
                        try:
                            await member.ban(reason="Anti-Nuke: Bot added by user who exceeded limit")
                        except:
                            pass
                    break
    
    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        async for entry in after.audit_logs(limit=1, action=discord.AuditLogAction.guild_update):
            await self.check_and_punish(after, entry.user, 'updating_server', f"Updated server settings")
            break
    
    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.webhook_create):
            was_punished = await self.check_and_punish(channel.guild, entry.user, 'creating_webhooks', f"Created webhook in #{channel.name}")
            if was_punished:
                try:
                    webhook = entry.target
                    await webhook.delete(reason="Anti-Nuke: Unauthorized webhook creation")
                except:
                    pass
            break
        
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.webhook_delete):
            await self.check_and_punish(channel.guild, entry.user, 'deleting_webhooks', f"Deleted webhook")
            break
    
    @commands.Cog.listener()
    async def on_guild_integrations_update(self, guild):
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.integration_create):
            await self.check_and_punish(guild, entry.user, 'authorizing_applications', f"Authorized application")
            break

import asyncio

async def setup(bot):
    await bot.add_cog(Protection(bot))
