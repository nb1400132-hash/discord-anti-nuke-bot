import discord
from discord.ext import commands
import asyncio
from utils.database import Database

TOKEN = 'YOUR_BOT_TOKEN_HERE'
APPLICATION_ID = None

intents = discord.Intents.all()

class AntiNukeBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            application_id=APPLICATION_ID
        )
        self.db = Database()
        
    async def setup_hook(self):
        await self.db.initialize()
        
        cogs = [
            'cogs.setlimit',
            'cogs.settime',
            'cogs.setpunishment',
            'cogs.whitelist',
            'cogs.unwhitelist',
            'cogs.addadmin',
            'cogs.saveserversettings',
            'cogs.loadfromsave',
            'cogs.protection'
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f'✓ Loaded {cog}')
            except Exception as e:
                print(f'✗ Failed to load {cog}: {e}')
        
        await self.tree.sync()
        print(f'✓ Synced {len(await self.tree.sync())} commands')
    
    async def on_ready(self):
        print(f'\n{"="*50}')
        print(f'Bot: {self.user.name}')
        print(f'ID: {self.user.id}')
        print(f'Servers: {len(self.guilds)}')
        print(f'{"="*50}\n')
        
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for threats | /help"
        )
        await self.change_presence(activity=activity, status=discord.Status.dnd)

bot = AntiNukeBot()

if __name__ == '__main__':
    if not TOKEN or TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print('Error: Please set your bot token in bot.py (TOKEN variable)')
    else:
        bot.run(TOKEN)
