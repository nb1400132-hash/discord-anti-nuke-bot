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
- **Custom Limits**: Set different limits for each action type (1 to infinity)
- **Time Windows**: Configure action timeframes (seconds, minutes, hours, days, weeks, months, years)
- **Multiple Punishments**: Choose from ban, kick, role removal, timeout, or warn
- **Whitelist System**: Exempt trusted users from all punishments
- **Admin System**: Grant users permission to modify anti-nuke settings

### 🎯 Smart Detection
- Tracks actions in real-time using audit logs
- Time-based action counting with configurable windows
- Automatic cleanup of old action logs
- Detects bot additions and tracks who added them
- Identifies dangerous permission grants (administrator, ban, kick, etc.)

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

1. **Action Detection**: The bot monitors server audit logs for specific actions
2. **Rate Tracking**: Each action is logged with a timestamp
3. **Limit Checking**: When an action occurs, the bot counts recent actions within the timeframe
4. **Punishment**: If the count exceeds the limit, the configured punishment is applied
5. **Whitelist Protection**: Server owner and whitelisted users are immune
6. **Bot Protection**: When a bot is added and the limit is exceeded, both the bot and the user who added it are punished

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
- Ban anyone who bans more than 3 members in 1 minute
- Ban anyone who deletes more than 5 channels in 30 seconds
- Ban anyone who adds more than 1 bot per hour (and remove the bot)
- Exempt TrustedModerator from all punishments

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
- `cogs/protection.py` - Core protection system with event listeners

## Security Features

- **Owner Immunity**: Server owner cannot be punished
- **Whitelist System**: Trusted users can be exempted
- **Role Hierarchy**: Bot respects role hierarchy (won't punish higher roles)
- **Audit Log Based**: All detections based on official Discord audit logs
- **No Bypass**: Permissions are checked on every command execution
- **Bot Tracking**: Tracks which user added each bot for accountability

## License

MIT License - Feel free to use and modify for your server protection needs.
