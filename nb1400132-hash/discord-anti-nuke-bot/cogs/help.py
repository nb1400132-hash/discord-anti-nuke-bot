import discord
from discord import app_commands
from discord.ext import commands


class HelpView(discord.ui.View):
    def __init__(self, pages: list[discord.Embed], author_id: int):
        super().__init__(timeout=120)
        self.pages = pages
        self.current = 0
        self.author_id = author_id
        self._update_buttons()

    def _update_buttons(self):
        self.prev_btn.disabled = self.current == 0
        self.next_btn.disabled = self.current == len(self.pages) - 1
        self.page_btn.label = f"{self.current + 1} / {len(self.pages)}"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Only the command user can navigate this help menu.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

    @discord.ui.button(label="1 / 1", style=discord.ButtonStyle.primary, disabled=True)
    async def page_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _footer(self, guild):
        return {"text": "VO AntiNuke • Help", "icon_url": guild.me.display_avatar.url if guild else None}

    @app_commands.command(name="help", description="📖 View all commands and usage")
    async def help(self, interaction: discord.Interaction):
        guild = interaction.guild
        footer = self._footer(guild)

        # Page 1: Overview
        page1 = discord.Embed(
            title="🛡️ VO AntiNuke — Help",
            description=(
                "A powerful anti-nuke and moderation bot. Use **◀ ▶** to navigate.\n\n"
                "**Pages:**\n"
                "```\n"
                "📖 Page 1 — Overview\n"
                "🛡️ Page 2 — Anti-Nuke Config\n"
                "🔨 Page 3 — Moderation\n"
                "⚠️ Page 4 — Warning System\n"
                "🔒 Page 5 — Jail System\n"
                "⚙️ Page 6 — Bot Configuration\n"
                "```"
            ),
            color=0x5865f2,
            timestamp=discord.utils.utcnow()
        )
        page1.add_field(
            name="ℹ️ Quick Info",
            value=(
                "• All commands are **slash commands** (`/command`)\n"
                "• Prefix commands use the server's configured prefix\n"
                "• `[optional]` = optional  •  `<required>` = required"
            ),
            inline=False
        )
        page1.set_footer(**footer)

        # Page 2: Anti-Nuke
        page2 = discord.Embed(
            title="🛡️ Anti-Nuke Configuration",
            description="Configure the anti-nuke protection system.",
            color=0xff4444,
            timestamp=discord.utils.utcnow()
        )
        for name, desc in [
            ("</setlimit:0>", "`/setlimit <action> <limit>` — Max times an action can occur before punishment"),
            ("</settime:0>", "`/settime <action> <timeframe>` — Timeframe window for action tracking"),
            ("</setpunishment:0>", "`/setpunishment <action> <punishment>` — Punishment for exceeding a limit"),
            ("</whitelist:0>", "`/whitelist <user>` — Exempt a user from anti-nuke checks"),
            ("</unwhitelist:0>", "`/unwhitelist <user>` — Remove a user from the whitelist"),
            ("</addadmin:0>", "`/addadmin <user>` — Grant bot admin privileges"),
            ("</saveserversettings:0>", "`/saveserversettings` — Save full server backup (channels, roles, emojis)"),
            ("</loadfromsave:0>", "`/loadfromsave` — Restore server from last saved backup"),
        ]:
            page2.add_field(name=name, value=desc, inline=False)
        page2.set_footer(**footer)

        # Page 3: Moderation
        page3 = discord.Embed(
            title="🔨 Moderation Commands",
            description="Commands for moderating your server.",
            color=0xff6600,
            timestamp=discord.utils.utcnow()
        )
        for name, desc in [
            ("</ban:0> — Ban a member", "`/ban <user> [reason] [delete_messages]`\n**Requires:** Ban Members\nBans a user. DMs them before banning with full details."),
            ("</kick:0> — Kick a member", "`/kick <user> [reason]`\n**Requires:** Kick Members\nKicks a user and DMs them the reason."),
            ("</nuke:0> — Nuke a channel", "`/nuke [channel]`\n**Requires:** Administrator or Manage Channels\nClones the channel and deletes the original, wiping all messages. Requires confirmation button."),
        ]:
            page3.add_field(name=name, value=desc, inline=False)
        page3.set_footer(**footer)

        # Page 4: Warnings
        page4 = discord.Embed(
            title="⚠️ Warning System",
            description="Manage member warnings. Stored in a dedicated `warns.db`.",
            color=0xffcc00,
            timestamp=discord.utils.utcnow()
        )
        for name, desc in [
            ("</warn:0>", "`/warn <user> [reason]`\n**Requires:** Manage Messages\nIssues a warning. DMs the user and logs with a unique ID."),
            ("</warnings:0>", "`/warnings <user>`\n**Requires:** Manage Messages\nShows all warnings on record for a user."),
            ("</removewarn:0>", "`/removewarn <warn_id>`\n**Requires:** Manage Messages\nRemoves a specific warning by ID."),
            ("</clearwarns:0>", "`/clearwarns <user>`\n**Requires:** Manage Messages\nClears every warning for a user."),
        ]:
            page4.add_field(name=name, value=desc, inline=False)
        page4.set_footer(**footer)

        # Page 5: Jail
        page5 = discord.Embed(
            title="🔒 Jail System",
            description="Full jail system with role management and auto-expiry. Stored in `jail.db`.",
            color=0xff6600,
            timestamp=discord.utils.utcnow()
        )
        for name, desc in [
            ("</setjailchannel:0> — Setup jail", "`/setjailchannel [channel]`\n**Requires:** Administrator\nSets up the jail channel. Auto-creates the Jailed role, locks all other channels from jailed users. If no channel is specified, one is created automatically."),
            ("</jail:0> — Jail a member", "`/jail <user> [reason] [duration]`\n**Requires:** Manage Roles\nJails a user — removes all their roles, adds the Jailed role. Duration is optional (e.g. `1h`, `30m`, `1d`). Permanent if omitted. Roles are safely stored in DB for restoration."),
            ("</unjail:0> — Unjail a member", "`/unjail <user> [reason]`\n**Requires:** Manage Roles\nUnjails a user and restores ALL their previous roles automatically."),
            ("</jaillist:0> — View jailed members", "`/jaillist`\n**Requires:** Manage Roles\nShows all currently jailed members with reason, moderator, duration and expiry."),
        ]:
            page5.add_field(name=name, value=desc, inline=False)
        page5.set_footer(**footer)

        # Page 6: Config
        page6 = discord.Embed(
            title="⚙️ Bot Configuration",
            description="Configure the bot for your server.",
            color=0x57f287,
            timestamp=discord.utils.utcnow()
        )
        for name, desc in [
            ("</changeprefix:0>", "`/changeprefix <prefix>`\n**Requires:** Server Owner\nChanges the bot's prefix (e.g. `!`, `?`, `.`). Slash commands are unaffected."),
            ("</moderationlog:0>", "`/moderationlog <channel>`\n**Requires:** Administrator or Bot Admin\nSets the channel for all moderation and anti-nuke action logs."),
            ("</invite:0>", "`/invite`\nGenerates the bot's invite link with Administrator permissions."),
            ("</help:0>", "`/help`\nShows this paginated help menu."),
        ]:
            page6.add_field(name=name, value=desc, inline=False)
        page6.set_footer(**footer)

        pages = [page1, page2, page3, page4, page5, page6]
        view = HelpView(pages, interaction.user.id)
        await interaction.response.send_message(embed=pages[0], view=view)


async def setup(bot):
    await bot.add_cog(Help(bot))