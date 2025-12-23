# Discord Anti-Nuke Bot

A powerful Discord anti-nuke bot built with discord.py that prevents server raids and unauthorized actions through intelligent rate limiting and automated punishment systems.

## Features

### 🛡️ Comprehensive Protection
- **Ban/Kick/Prune Prevention**: Monitors and limits member removal actions
- **Channel Protection**: Prevents mass channel creation/deletion/editing
- **Role Protection**: Stops unauthorized role creation/deletion/modification
- **Permission Protection**: Detects and prevents dangerous permission grants
- **Bot Protection**: Monitors bot additions and removes malicious bots
- **Webhook Protection**: Prevents unauthorized webhook creation/deletion
- **Server Protection**: Monitors server settings changes

### ⚙️ Flexible Configuration
- **Custom Limits**: Set different limits for each action type (0 to infinity)
  - Setting limit to 0 = instant punishment for any action
- **Time Windows**: Configure action timeframes (seconds, minutes, hours, days, weeks, months, years)
- **Multiple Punishments**: Choose from ban, kick, role removal, timeout, or warn
- **Whitelist System**: Exempt trusted users from all punishments
- **Admin System**: Grant users permission to modify anti-nuke settings
- **Backup System**: Save and restore complete server state (channels, roles, emojis, settings)

### 🎯 Smart Detection
- Tracks actions in real-time using audit logs
- Time-based action counting with configurable windows
- Automatic cleanup of old action logs
- Detects bot additions and tracks who added them
- Identifies dangerous permission grants (administrator, ban, kick, etc.)

### 💾 Server Backup & Recovery
- **Complete Backup**: Save entire server state with one command
- **Instant Restore**: Restore server from backup after a nuke attack
- **Smart Overwrite**: Warns before overwriting existing backups
- **Confirmation System**: Requires double confirmation for destructive operations
- **Progress Tracking**: Shows real-time progress during restoration
- **Unique Identification**: Each backup is tied to specific server ID

### 🔄 Advanced Revert System
- **Auto-Restore Channels**: Recreates deleted channels with original permissions, position, and settings
- **Auto-Delete Unauthorized Channels**: Removes channels created by nukers
- **Auto-Restore Roles**: Recreates deleted roles with original permissions, color, and position
- **Auto-Delete Unauthorized Roles**: Removes roles created by nukers
- **Auto-Unban**: Unbans members who were banned by nukers exceeding limits
- **Server Settings Revert**: Restores server name and vanity URL changes
- **State Caching**: Automatically caches all channels and roles every 5 minutes for accurate restoration
- **Higher-Role Protection**: Even if a bot/user has higher roles than the anti-nuke bot, it will still revert their destructive actions (channel/role deletion) to buy time for the owner

## Commands

All commands use Discord's slash command system for a modern, user-friendly experience.

### Owner/Admin Commands

#### `/setlimit`
Set the maximum number of times an action can be performed within the timeframe.
- **Parameters:**
  - `action`: The action to limit (banning, kicking, creating channels, etc.)
  - `limit`: Maximum number of times (1 to infinity)
- **Example:** `/setlimit action:Banning Members limit:3`

#### `/settime`
Set the timeframe for action limits.
- **Parameters:**
  - `action`: The action to set a timeframe for
  - `timeframe`: Time format (1s, 1m, 1h, 1d, 1w, 1mo, 1y)
- **Example:** `/settime action:Creating Channels timeframe:5m`
- **Format:**
  - `s` = seconds
  - `m` = minutes
  - `h` = hours
  - `d` = days
  - `w` = weeks
  - `mo` = months
  - `y` = years

#### `/setpunishment`
Set the punishment for exceeding action limits.
- **Parameters:**
  - `action`: The action to set a punishment for
  - `punishment`: The punishment type (ban, kick, clear_roles, timeout, warn)
- **Example:** `/setpunishment action:Adding Bots punishment:ban`

### Owner-Only Commands

#### `/whitelist`
Make a user immune to anti-nuke punishments.
- **Parameters:**
  - `user`: User mention, ID, or username
- **Example:** `/whitelist user:@TrustedAdmin`

#### `/unwhitelist`
Remove a user from the whitelist.
- **Parameters:**
  - `user`: User mention, ID, or username
- **Example:** `/unwhitelist user:@FormerAdmin`

#### `/addadmin`
Grant a user permission to modify anti-nuke settings.
- **Parameters:**
  - `user`: User mention, ID, or username
- **Example:** `/addadmin user:@ModeratorName`

### Backup Commands (Owner/Admin)

#### `/saveserversettings`
Save complete server backup (channels, roles, emojis, settings).
- **What it saves:**
  - All channels with permissions, settings, and positions
  - All roles with permissions, colors, and positions
  - All emojis
  - Server name, vanity URL, description
- **Features:**
  - Only 1 save per server (overwrites previous)
  - Confirmation required when overwriting
  - Only owner and admins can use
- **Example:** `/saveserversettings`

#### `/loadfromsave`
Restore server from backup (WARNING: Deletes all current content first).
- **What it does:**
  1. Deletes all current channels and roles
  2. Restores server name and vanity URL
  3. Recreates all roles with exact permissions
  4. Recreates all channels with exact permissions
  5. Restores categories and channel positions
- **Features:**
  - Requires confirmation (run twice within 60 seconds)
  - Only works with backup for that specific server
  - Shows progress for each restoration step
  - Only owner and admins can use
- **Use case:** Quickly restore server after a nuke attack
- **Example:** `/loadfromsave`

## Monitored Actions

The bot monitors and can limit the following actions:

- **Banning Members** - When members are banned
- **Kicking Members** - When members are kicked
- **Pruning Members** - When inactive members are pruned
- **Creating Channels** - When new channels are created
- **Deleting Channels** - When channels are deleted
- **Editing Channels** - When channel settings are modified
- **Creating Roles** - When new roles are created
- **Deleting Roles** - When roles are deleted
- **Editing Roles** - When role settings are modified
- **Giving Dangerous Permissions** - When roles with ban/kick/manage permissions are granted
- **Giving Administrative Roles** - When administrator permission is granted
- **Adding Bots** - When bots are invited to the server
- **Updating Server** - When server settings are changed
- **Creating Webhooks** - When webhooks are created
- **Deleting Webhooks** - When webhooks are deleted
- **Authorizing Applications** - When OAuth2 applications are authorized

## Punishment Types

- **Ban** - Permanently bans the user from the server
- **Kick** - Kicks the user from the server
- **Clear Roles** - Removes all roles from the user
- **Timeout** - Times out the user for 1 day
- **Warn** - Logs a warning (no action taken)

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on `.env.example`:
   ```
   TOKEN=your_bot_token_here
   APPLICATION_ID=your_application_id_here
   ```

4. Run the bot:
   ```bash
   python bot.py
   ```

## Bot Permissions

The bot requires the following permissions to function properly:

- View Audit Log
- Kick Members
- Ban Members
- Manage Roles
- Manage Channels
- Manage Server
- Manage Webhooks
- View Channels
- Send Messages
- Embed Links
- Moderate Members (for timeout)

## How It Works

1. **State Caching**: Every 5 minutes, the bot caches all channels, roles, and server settings with full details (permissions, positions, colors, etc.)
2. **Action Detection**: The bot monitors server audit logs in real-time for specific actions
3. **Rate Tracking**: Each action is logged with a timestamp in the database
4. **Limit Checking**: When an action occurs, the bot counts recent actions within the configured timeframe
5. **Punishment & Revert**: If the count exceeds the limit:
   - If the user has a lower role than the bot: Apply configured punishment (ban/kick/clear roles/timeout)
   - If the user has a higher role than the bot: Cannot punish but will still revert destructive actions
   - **Revert Actions**: Automatically undo destructive changes:
     - Deleted channels → Recreated with original permissions, position, settings
     - Created channels → Deleted immediately
     - Deleted roles → Recreated with original permissions, color, position
     - Created roles → Deleted immediately
     - Banned members → Unbanned
     - Server name/vanity changes → Reverted to previous values
6. **Whitelist Protection**: Server owner and whitelisted users are immune to all checks
7. **Bot Protection**: When a bot is added and the limit is exceeded, both the bot and the user who added it are punished

## Example Configuration

To protect against server nuking:

```
/setlimit action:Banning Members limit:3
/settime action:Banning Members timeframe:1m
/setpunishment action:Banning Members punishment:ban

/setlimit action:Deleting Channels limit:5
/settime action:Deleting Channels timeframe:30s
/setpunishment action:Deleting Channels punishment:ban

/setlimit action:Adding Bots limit:1
/settime action:Adding Bots timeframe:1h
/setpunishment action:Adding Bots punishment:ban

/whitelist user:@TrustedModerator
```

This configuration will:
- Ban anyone who bans more than 3 members in 1 minute (and unban the victims)
- Ban anyone who deletes more than 5 channels in 30 seconds (and recreate the deleted channels with original permissions)
- Ban anyone who adds more than 1 bot per hour (and remove the bot)
- Exempt TrustedModerator from all punishments

**Even if a rogue admin/bot has higher roles than the anti-nuke bot**, it will still:
- Recreate any deleted channels with full permissions
- Delete any unauthorized created channels
- Recreate any deleted roles
- Delete any unauthorized created roles
- Unban any banned members
- Revert server name and vanity URL changes
- Alert the server owner so they can come online and handle the situation

## Architecture

The bot is built with a modular cog system:

- `bot.py` - Main bot file with initialization
- `utils/database.py` - SQLite database handler for persistent storage
- `utils/checks.py` - Permission checking decorators
- `utils/helpers.py` - Helper functions for time parsing and formatting
- `cogs/setlimit.py` - Limit configuration command
- `cogs/settime.py` - Timeframe configuration command
- `cogs/setpunishment.py` - Punishment configuration command
- `cogs/whitelist.py` - Whitelist management command
- `cogs/unwhitelist.py` - Whitelist removal command
- `cogs/addadmin.py` - Admin management command
- `cogs/saveserversettings.py` - Server backup command with overwrite confirmation
- `cogs/loadfromsave.py` - Server restore command with double confirmation
- `cogs/protection.py` - Core protection system with event listeners, state caching, and revert logic

## Security Features

- **Owner Immunity**: Server owner cannot be punished
- **Whitelist System**: Trusted users can be exempted
- **Role Hierarchy Aware**: Bot respects role hierarchy (won't punish higher roles but WILL revert their destructive actions)
- **Higher-Role Mitigation**: Even if attacker has higher role, bot will revert channel/role deletions and creations to prevent nuke damage
- **Audit Log Based**: All detections based on official Discord audit logs
- **No Bypass**: Permissions are checked on every command execution
- **Bot Tracking**: Tracks which user added each bot for accountability
- **State Persistence**: Caches server state every 5 minutes to enable accurate restoration
- **Automatic Revert**: Instantly undoes destructive actions (unbans, recreates channels/roles, restores settings)
- **Complete Restoration**: Recreates channels and roles with exact permissions, positions, colors, and settings

## License

MIT License - Feel free to use and modify for your server protection needs.
