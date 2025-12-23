import aiosqlite
import os

class Database:
    def __init__(self):
        self.db_path = 'data/antinuke.db'
        
    async def initialize(self):
        os.makedirs('data', exist_ok=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS limits (
                    guild_id INTEGER,
                    action TEXT,
                    limit INTEGER,
                    PRIMARY KEY (guild_id, action)
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS timeframes (
                    guild_id INTEGER,
                    action TEXT,
                    seconds INTEGER,
                    PRIMARY KEY (guild_id, action)
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS punishments (
                    guild_id INTEGER,
                    action TEXT,
                    punishment TEXT,
                    PRIMARY KEY (guild_id, action)
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS whitelist (
                    guild_id INTEGER,
                    user_id INTEGER,
                    PRIMARY KEY (guild_id, user_id)
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    guild_id INTEGER,
                    user_id INTEGER,
                    PRIMARY KEY (guild_id, user_id)
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS action_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    action TEXT,
                    timestamp INTEGER
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS bot_owners (
                    guild_id INTEGER,
                    bot_id INTEGER,
                    owner_id INTEGER,
                    PRIMARY KEY (guild_id, bot_id)
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS server_backups (
                    guild_id INTEGER PRIMARY KEY,
                    backup_data TEXT,
                    timestamp INTEGER
                )
            ''')
            
            await db.commit()
    
    async def set_limit(self, guild_id: int, action: str, limit: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT OR REPLACE INTO limits (guild_id, action, limit) VALUES (?, ?, ?)',
                (guild_id, action, limit)
            )
            await db.commit()
    
    async def get_limit(self, guild_id: int, action: str):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT limit FROM limits WHERE guild_id = ? AND action = ?',
                (guild_id, action)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
    
    async def set_timeframe(self, guild_id: int, action: str, seconds: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT OR REPLACE INTO timeframes (guild_id, action, seconds) VALUES (?, ?, ?)',
                (guild_id, action, seconds)
            )
            await db.commit()
    
    async def get_timeframe(self, guild_id: int, action: str):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT seconds FROM timeframes WHERE guild_id = ? AND action = ?',
                (guild_id, action)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 60
    
    async def set_punishment(self, guild_id: int, action: str, punishment: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT OR REPLACE INTO punishments (guild_id, action, punishment) VALUES (?, ?, ?)',
                (guild_id, action, punishment)
            )
            await db.commit()
    
    async def get_punishment(self, guild_id: int, action: str):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT punishment FROM punishments WHERE guild_id = ? AND action = ?',
                (guild_id, action)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 'ban'
    
    async def add_whitelist(self, guild_id: int, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT OR IGNORE INTO whitelist (guild_id, user_id) VALUES (?, ?)',
                (guild_id, user_id)
            )
            await db.commit()
    
    async def remove_whitelist(self, guild_id: int, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'DELETE FROM whitelist WHERE guild_id = ? AND user_id = ?',
                (guild_id, user_id)
            )
            await db.commit()
    
    async def is_whitelisted(self, guild_id: int, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT 1 FROM whitelist WHERE guild_id = ? AND user_id = ?',
                (guild_id, user_id)
            ) as cursor:
                return await cursor.fetchone() is not None
    
    async def add_admin(self, guild_id: int, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT OR IGNORE INTO admins (guild_id, user_id) VALUES (?, ?)',
                (guild_id, user_id)
            )
            await db.commit()
    
    async def is_admin(self, guild_id: int, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT 1 FROM admins WHERE guild_id = ? AND user_id = ?',
                (guild_id, user_id)
            ) as cursor:
                return await cursor.fetchone() is not None
    
    async def log_action(self, guild_id: int, user_id: int, action: str, timestamp: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT INTO action_log (guild_id, user_id, action, timestamp) VALUES (?, ?, ?, ?)',
                (guild_id, user_id, action, timestamp)
            )
            await db.commit()
    
    async def get_recent_actions(self, guild_id: int, user_id: int, action: str, since_timestamp: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT COUNT(*) FROM action_log WHERE guild_id = ? AND user_id = ? AND action = ? AND timestamp >= ?',
                (guild_id, user_id, action, since_timestamp)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0
    
    async def cleanup_old_logs(self, guild_id: int, before_timestamp: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'DELETE FROM action_log WHERE guild_id = ? AND timestamp < ?',
                (guild_id, before_timestamp)
            )
            await db.commit()
    
    async def set_bot_owner(self, guild_id: int, bot_id: int, owner_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT OR REPLACE INTO bot_owners (guild_id, bot_id, owner_id) VALUES (?, ?, ?)',
                (guild_id, bot_id, owner_id)
            )
            await db.commit()
    
    async def get_bot_owner(self, guild_id: int, bot_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT owner_id FROM bot_owners WHERE guild_id = ? AND bot_id = ?',
                (guild_id, bot_id)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
    
    async def save_server_backup(self, guild_id: int, backup_data: str, timestamp: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT OR REPLACE INTO server_backups (guild_id, backup_data, timestamp) VALUES (?, ?, ?)',
                (guild_id, backup_data, timestamp)
            )
            await db.commit()
    
    async def get_server_backup(self, guild_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT backup_data, timestamp FROM server_backups WHERE guild_id = ?',
                (guild_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return result if result else None
    
    async def has_server_backup(self, guild_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT 1 FROM server_backups WHERE guild_id = ?',
                (guild_id,)
            ) as cursor:
                return await cursor.fetchone() is not None
