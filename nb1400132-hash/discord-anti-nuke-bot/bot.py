import discord
from discord.ext import commands
import asyncio
from utils.database import Database
from utils.warns_database import WarnsDatabase
from utils.jail_database import JailDatabase

TOKEN = 'put your token here :)'
APPLICATION_ID = 1 

intents = discord.Intents.all()


async def get_prefix(bot, message):
    """Dynamic per-guild prefix, falls back to '!'"""
    if message.guild:
        prefix = await bot.db.get_prefix(message.guild.id)
        return prefix or '!'
    return '!'


class AntiNukeBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            application_id=APPLICATION_ID,
            help_command=None  # Custom /help slash command
        )
        self.db = Database()
        self.warns_db = WarnsDatabase()
        self.jail_db = JailDatabase()

    async def setup_hook(self):
        # Initialize all databases
        await self.db.initialize()
        await self.warns_db.initialize()
        await self.jail_db.initialize()

        cogs = [
            # Anti-nuke core
            'cogs.setlimit',
            'cogs.settime',
            'cogs.setpunishment',
            'cogs.whitelist',
            'cogs.unwhitelist',
            'cogs.addadmin',
            'cogs.saveserversettings',
            'cogs.loadfromsave',
            'cogs.protection',
            # Moderation
            'cogs.ban',
            'cogs.kick',
            'cogs.warn',
            'cogs.nuke',
            'cogs.jail',
            # Configuration
            'cogs.changeprefix',
            'cogs.moderationlog',
            'cogs.invite',
            # Help
            'cogs.help',
            # Settings
            'cogs.antinukesettings',
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f'✓ Loaded {cog}')
            except Exception as e:
                print(f'✗ Failed to load {cog}: {e}')

        synced = await self.tree.sync()
        print(f'✓ Synced {len(synced)} slash commands')

    async def on_ready(self):
        print(f'\n{"=" * 50}')
        print(f'Bot:     {self.user.name}')
        print(f'ID:      {self.user.id}')
        print(f'Servers: {len(self.guilds)}')
        print(f'{"=" * 50}\n')

        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for threats | /help"
        )
        await self.change_presence(activity=activity, status=discord.Status.dnd)


bot = AntiNukeBot()

if __name__ == '__main__':
    if not TOKEN or TOKEN == '':
        print('Error: Please set your bot token in bot.py (TOKEN variable)')
    else:
        bot.run(TOKEN)
