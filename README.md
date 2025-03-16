# XGC Crypto Discord Bot

A Discord bot designed specifically for crypto communities with features including account verification, role management, moderation tools, welcome/goodbye messages, and advanced server setup with role-based permission management.

## Features

### 1. Account Verification
- Reaction-based verification system
- Auto-DM instructions to new members
- Custom verification messages

### 2. Role Management
- Manual role assignment by moderators
- Self-assignable roles for members
- Role hierarchy management

### 3. Moderation Tools
- Kick and ban commands
- Message clearing functionality
- Logging system for moderator actions

### 4. Welcome/Goodbye Messages
- Automatic welcome messages for new members
- Goodbye messages when members leave
- Customizable message templates

### 5. Server Setup
- Advanced server setup tools for creating a complete crypto server structure
- Automatic configuration of channel permissions
- Role-based access control for channels
- Granular permission management for roles and channels
- Channel grouping for bulk permission management
- One-command server permission setup for standardized role hierarchies

## Setup Instructions

1. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root with the following variables:
   ```
   DISCORD_TOKEN=your_discord_bot_token
   WELCOME_CHANNEL_ID=your_welcome_channel_id
   VERIFICATION_CHANNEL_ID=your_verification_channel_id
   VERIFICATION_MESSAGE_ID=your_verification_message_id
   VERIFIED_ROLE_ID=your_verified_role_id
   MOD_ROLE_ID=your_mod_role_id
   ```

3. Create the following roles in your Discord server:
   - Verified (for verified members)
   - Trader (self-assignable)
   - HODLer (self-assignable)
   - Analyst (self-assignable)
   - Developer (self-assignable)
   - Investor (self-assignable)

4. Run the bot:
   ```
   python bot.py
   ```

5. Use the `!setup_verification` command to create a verification message in your verification channel

## Commands

### General Commands
- `!getrole [role]` - Self-assign a role from available roles
- `!ping` - Check bot latency
- `!info` - Show server information
- `!botinfo` - Show bot information
- `!crypto` - Display crypto disclaimer

### Role Management
- `!role @user [role]` - Assign a role to a user (mod only)
- `!assign_role @user [role]` - Assign a role to a user (mod only)
- `!remove_role @user [role]` - Remove a role from a user (mod only)
- `!has_permission @user [permission]` - Check if a user has a specific permission
- `!has_role @user [role]` - Check if a user has a specific role

### Moderation Commands
- `!kick @user [reason]` - Kick a user from the server (mod only)
- `!ban @user [reason]` - Ban a user from the server (mod only)
- `!clear [amount]` - Clear a specific number of messages from a channel (mod only)

### Advanced Permission Commands (Admin Only)
- `!channels` - View available channel management commands
- `!channels list` - List all channel groups and their channels
- `!channels create_group <name>` - Create a new channel group
- `!channels add_to_group <group_name> <#channel> [#channel2 ...]` - Add channels to a group
- `!channels remove_from_group <group_name> <#channel> [#channel2 ...]` - Remove channels from a group
- `!channels set_group_permission <group_name> <role_name> <permission> <true/false>` - Set permission for a role
- `!channels set_permission <#channel> <role_name> <permission> <true/false>` - Set permission for a specific channel
- `!channels apply_permissions` - Apply all permission settings
- `!channels set_public <#channel> [#channel2 ...]` - Make channels visible to everyone
- `!channels set_verified_only <#channel> [#channel2 ...]` - Make channels visible only to verified users
- `!channels all_verified_only <#channel> [#channel2 ...]` - Make all channels verified-only except the specified channels
- `!channels info [#channel]` - Show permission details for a channel
- `!channels role view <role>` - View permissions for a role across all channels
- `!channels role allow <role> <permission> <#channel> [#channel2 ...]` - Allow a permission for a role
- `!channels role deny <role> <permission> <#channel> [#channel2 ...]` - Deny a permission for a role
- `!channels role reset <role> <permission> <#channel> [#channel2 ...]` - Reset a permission for a role
- `!channels role copy <from_role> <to_role> [#channel]` - Copy permissions from one role to another
- `!channels preset <preset_name>` - Apply a preset permission configuration (crypto, community, minimal)
- `!channels lockdown <mode>` - Lock down server to prevent spam (all, public, verified, unlock)
- `!channels setup_xgc_permissions` - Automatically set up a complete XGC server permission structure with role hierarchy
- `!quicksetup` - Automatically set up default channel groups and permissions

### Server Setup Commands (Admin Only)
- `!setup server` - Create a basic crypto server structure with categories and channels
- `!setup permissions` - Set up permissions for verified/unverified users
- `!create_category "Category Name"` - Create a new category with proper permissions
- `!create_channel "Category Name" "channel-name" [public]` - Create a new channel in a category
- `!add_role_to_channels "Role Name" ["Category Name"] [can_view=True] [can_send=True]` - Set channel permissions for a specific role

## XGC Permission Structure

The `!channels setup_xgc_permissions` command configures a complete permission structure based on the following role hierarchy:

### Role Hierarchy
1. **New Users** (unverified)
   - Can only see specific public channels (Verification, Welcome, Rules, Total Members, XRP Price)
   - Can only send messages in verification channel

2. **Verified Users**
   - Can see all general channels
   - Cannot see mod channels or alpha channels
   - Cannot type in information channels

3. **NFT Holders**
   - All Verified User permissions
   - Can access Alpha Chat channels

4. **XGC (Bots)**
   - All NFT Holder permissions
   - Can access mod channels

5. **Moderators**
   - Full access to all channels except bot-only sections
   - Can post in information channels

6. **Admins**
   - Full access to everything

### Channel Categories
The command automatically categorizes channels into:

- **Public** - `verification`, `welcome`, `rules`, `total-members`, `xrp-price`
- **Information** - `welcome`, `rules`, `roles`, `xgc-news`
- **General** - `general`, `voice-channels`, `raids`, `giveaways`, `game-nights`, `project-hub`
- **Alpha** - `alpha-chat`
- **Mod** - `bot-logs`, `modlog`, `testing`
- **Bot** - `bot-logs`

### Usage Example
To automatically set up the entire server permission structure:
```
!channels setup_xgc_permissions
```

This single command will:
1. Create any missing roles (NFT Holder, XGC, Moderator, Admin)
2. Assign appropriate colors to these roles
3. Categorize all channels based on their names
4. Apply all permissions according to the role hierarchy
5. Show a summary of what was configured

## Server Setup Features

The bot includes advanced server setup tools that make it easy to:

1. **Manage Channel Permissions** - Automatically configure who can see which channels
2. **Create Server Structure** - Set up a complete server structure with one command
3. **Role-Based Access Control** - Control channel visibility based on roles

### Permission System

By default, the server setup creates:
- Public channels: Visible to everyone (verified and unverified users)
- Members-only channels: Only visible to verified users

This ensures:
- New users only see welcome/verification channels until they verify
- Verified users see all content
- Custom roles can have specific permissions per channel or category

### Quick Setup

Run `!setup server` to create a complete crypto server with the following structure:

- **INFORMATION** category (public)
  - welcome
  - rules
  - announcements
  - verification

- **COMMUNITY** category (verified only)
  - general
  - crypto-talk
  - trading
  - market-analysis

- **RESOURCES** category (verified only)
  - useful-links
  - tutorials
  - tools

- **BOT COMMANDS** category (verified only)
  - bot-commands

## Advanced Permission Management

The bot includes a powerful permission management system that allows you to:

### 1. Channel Groups

Create logical groups of channels that share the same permission settings:

```
!channels create_group trading
!channels add_to_group trading #bitcoin #ethereum #altcoins
```

### 2. Role-Specific Permissions

Give specific roles granular permissions on channels or channel groups:

```
!channels set_permission #bitcoin Analyst read_messages true
!channels set_permission #bitcoin Analyst send_messages true
!channels set_group_permission trading Trader read_messages true
```

### 3. Permission Types

Control various permission types individually:
- `read_messages` - Can see the channel
- `send_messages` - Can send messages
- `embed_links` - Can embed links
- `attach_files` - Can upload files
- `read_message_history` - Can read past messages
- `mention_everyone` - Can mention @everyone
- `add_reactions` - Can add reactions

### 4. Quick Setup

Automatically configure your server's permissions:

```
!quicksetup
```

This will:
1. Create default channel groups
2. Identify channels by name pattern (welcome, trading, etc.)
3. Assign appropriate permissions
4. Set up verified role permissions

### 5. Preset Configurations

Apply pre-made permission configurations to your server:

```
!channels preset crypto
```

Available presets:
- `crypto` - Configured for crypto community with trading, analysis, and news sections
- `community` - General community server with topic-based channels
- `minimal` - Basic server with just public/verified separation

## Advanced Usage

### Working with Channel IDs

All commands work with both channel mentions and IDs:

```
!channels set_permission #welcome Verified send_messages false
!channels set_permission 1234567890123456 Verified send_messages false
!channels set_public 9876543210987654
```

This is especially useful when:
- Discord's mention system isn't working well
- You want to script commands
- Channels are in different categories

### Debugging Permissions

To troubleshoot permission issues:

```
!channels info #channel-name
!channels role view "Role Name"
```

This shows all permission overwrites for a channel, helping identify conflicts or missing permissions.

### Permission Inheritance

The bot follows Discord's permission system:
1. Server-wide permissions (set in Server Settings > Roles)
2. Category permissions
3. Channel-specific permissions
4. User-specific permissions (not managed by the bot)

When using channel groups, permissions are applied directly to each channel, not at the category level.

## Creating Commands for XGC Bot

To extend the XGC bot with new commands, create Python files in the `cogs` directory following this structure:

1. Import required modules:
```python
import discord
from discord.ext import commands
```

2. Create a class that inherits from `commands.Cog`:
```python
class YourCogName(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
```

3. Define commands using the `@commands.command()` decorator:
```python
    @commands.command(name="your_command")
    async def your_command(self, ctx, arg1, arg2=None):
        """Command description for help text"""
        # Command logic here
        await ctx.send("Response to user")
```

4. Add a setup function to register the cog:
```python
def setup(bot):
    bot.add_cog(YourCogName(bot))
```

5. Load the cog in `bot.py` by adding:
```python
bot.load_extension("cogs.your_file_name")
```

### Permission Requirements

To restrict commands to specific roles or permissions:

```python
@commands.command(name="mod_only_command")
@commands.has_permissions(kick_members=True)
async def mod_only_command(self, ctx):
    # Command logic here
```

Or with custom role checks:
```python
@commands.command(name="admin_only")
@commands.has_role("Admin")
async def admin_only(self, ctx):
    # Command logic here
```

### Command Groups

For complex command sets with subcommands:

```python
@commands.group(name="parent")
async def parent(self, ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send("Please specify a subcommand")

@parent.command(name="child")
async def parent_child(self, ctx):
    await ctx.send("You used the child command")
```

This creates commands like `!parent child`.

### Error Handling

Add error handlers for graceful error management:

```python
@your_command.error
async def your_command_error(self, ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Error: Missing required argument")
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send(f"Error: {str(error)}")
```

For comprehensive documentation on Discord.py, visit the [official Discord.py documentation](https://discordpy.readthedocs.io/).
