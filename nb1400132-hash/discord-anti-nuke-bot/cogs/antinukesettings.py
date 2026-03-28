import discord
from discord import app_commands
from discord.ext import commands


ACTION_LABELS = {
    'banning_members':              ('🔨', 'Banning Members'),
    'kicking_members':              ('👢', 'Kicking Members'),
    'creating_channels':            ('📢', 'Creating Channels'),
    'deleting_channels':            ('🗑️', 'Deleting Channels'),
    'creating_roles':               ('🏷️', 'Creating Roles'),
    'deleting_roles':               ('❌', 'Deleting Roles'),
    'editing_channels':             ('✏️', 'Editing Channels'),
    'editing_roles':                ('📝', 'Editing Roles'),
    'giving_dangerous_permissions': ('⚠️', 'Giving Dangerous Permissions'),
    'giving_administrative_roles':  ('👑', 'Giving Admin Roles'),
    'adding_bots':                  ('🤖', 'Adding Bots'),
    'updating_server':              ('🌐', 'Updating Server'),
    'creating_webhooks':            ('🔗', 'Creating Webhooks'),
    'deleting_webhooks':            ('🔗', 'Deleting Webhooks'),
    'authorizing_applications':     ('🔌', 'Authorizing Applications'),
    'timing_out_members':           ('⏰', 'Timing Out Members'),
    'changing_nicknames':           ('📛', 'Changing Nicknames'),
    'pruning_members':              ('✂️', 'Pruning Members'),
}

PUNISHMENT_LABELS = {
    'ban':         '🔨 Ban',
    'kick':        '👢 Kick',
    'clear_roles': '🔓 Clear Roles',
    'timeout':     '⏰ Timeout',
    'warn':        '⚠️ Warn',
}


class AntiNukeSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="antinukesettings",
        description="🛡️ View the current Anti-Nuke protection settings for this server"
    )
    async def antinukesettings(self, interaction: discord.Interaction):
        is_bot_admin = await self.bot.db.is_admin(interaction.guild.id, interaction.user.id)
        has_perm = (
            interaction.user.guild_permissions.manage_guild
            or interaction.user.id == interaction.guild.owner_id
            or is_bot_admin
        )
        if not has_perm:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Access Denied",
                    description=(
                        "You need one of the following to use this command:\n"
                        "• **Manage Server** permission\n"
                        "• Server Owner\n"
                        "• Authorized bot admin (via `/addadmin`)"
                    ),
                    color=0xff0000
                ),
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=False)

        
        rows = []
        for action, (emoji, label) in ACTION_LABELS.items():
            limit     = await self.bot.db.get_limit(interaction.guild.id, action)
            timeframe = await self.bot.db.get_timeframe(interaction.guild.id, action)
            punishment = await self.bot.db.get_punishment(interaction.guild.id, action)

            limit_str      = str(limit)      if limit      is not None else '—'
            timeframe_str  = str(timeframe)  if timeframe  is not None else '—'
            punishment_str = PUNISHMENT_LABELS.get(punishment, punishment or '—')

            rows.append((emoji, label, limit_str, timeframe_str, punishment_str))

        
        embeds = []
        half = len(rows) // 2 + len(rows) % 2

        for chunk_index, chunk in enumerate([rows[:half], rows[half:]]):
            title = "🛡️ Anti-Nuke Settings" if chunk_index == 0 else "🛡️ Anti-Nuke Settings (cont.)"
            embed = discord.Embed(
                title=title,
                color=0x5865f2,
                timestamp=discord.utils.utcnow(),
            )

            if chunk_index == 0:
                embed.description = (
                    f"Protection configuration for **{interaction.guild.name}**.\n"
                    "Adjust any setting with `/setlimit`, `/settime`, or `/setpunishment`.\n\n"
                    "**Format:** `Max actions / Timeframe (s) → Punishment`"
                )

            for emoji, label, limit_str, timeframe_str, punishment_str in chunk:
                embed.add_field(
                    name=f"{emoji} {label}",
                    value=f"`{limit_str}` actions / `{timeframe_str}s` → {punishment_str}",
                    inline=True,
                )

            
            remainder = len(chunk) % 3
            if remainder != 0:
                for _ in range(3 - remainder):
                    embed.add_field(name="\u200b", value="\u200b", inline=True)

            embed.set_footer(
                text="VO AntiNuke • Protection System",
                icon_url=interaction.guild.me.display_avatar.url
            )
            embeds.append(embed)

        
        try:
            whitelist = await self.bot.db.get_whitelist(interaction.guild.id)
            whitelist_count = len(whitelist) if whitelist else 0
        except Exception:
            whitelist_count = 0

        log_channel_id = await self.bot.db.get_log_channel(interaction.guild.id)
        log_channel = interaction.guild.get_channel(log_channel_id) if log_channel_id else None
        log_channel_str = log_channel.mention if log_channel else '`Not set`'

        prefix = await self.bot.db.get_prefix(interaction.guild.id)
        prefix_str = f"`{prefix}`" if prefix else '`!`'

        summary_embed = discord.Embed(
            title="⚙️ Server Configuration",
            color=0x57f287,
            timestamp=discord.utils.utcnow(),
        )
        summary_embed.add_field(name="📋 Log Channel",         value=log_channel_str,          inline=True)
        summary_embed.add_field(name="✅ Whitelisted Users",    value=str(whitelist_count),      inline=True)
        summary_embed.add_field(name="🔤 Command Prefix",       value=prefix_str,               inline=True)
        summary_embed.set_footer(
            text="VO AntiNuke • Protection System",
            icon_url=interaction.guild.me.display_avatar.url
        )

        await interaction.followup.send(embeds=[*embeds, summary_embed])


async def setup(bot):
    await bot.add_cog(AntiNukeSettings(bot))