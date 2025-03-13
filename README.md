# XGC Crypto Discord Bot

A Discord bot designed specifically for crypto communities with features including account verification, role management, moderation tools, welcome/goodbye messages, and advanced server setup.

## Features

### 1. Account Verification
- Reaction-based verification system
- Auto-DM instructions to new members

### 2. Role Management
- Manual role assignment by moderators
- Self-assignable roles for members

### 3. Moderation Tools
- Kick and ban commands
- Message clearing functionality

### 4. Welcome/Goodbye Messages
- Automatic welcome messages for new members
- Goodbye messages when members leave

### 5. Server Setup
- Advanced server setup tools for creating a complete crypto server structure
- Automatic configuration of channel permissions
- Role-based access control for channels
- Granular permission management for roles and channels
- Channel grouping for bulk permission management

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
- `!quicksetup` - Automatically set up default channel groups and permissions

### Server Setup Commands (Admin Only)
- `!setup server` - Create a basic crypto server structure with categories and channels
- `!setup permissions` - Set up permissions for verified/unverified users
- `!create_category "Category Name"` - Create a new category with proper permissions
- `!create_channel "Category Name" "channel-name" [public]` - Create a new channel in a category
- `!add_role_to_channels "Role Name" ["Category Name"] [can_view=True] [can_send=True]` - Set channel permissions for a specific role

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
- `crypto` - Optimal configuration for crypto servers with trading channels
- `community` - General community server setup
- `minimal` - Minimal configuration with basic public/private separation

### 6. Role-Based Management

Manage permissions for roles across many channels at once:

```
!channels role allow Moderator manage_messages #mod-chat #admin-chat #support
!channels role deny Trader send_messages #announcements
!channels role copy Admin Moderator
```

### 7. Emergency Lockdown

Quickly lock down your server in case of spam or raids:

```
!channels lockdown all
```

Lockdown modes:
- `all`: Lock down all channels (default)
- `public`: Lock down only public channels
- `verified`: Lock down channels visible to verified users
- `unlock`: Remove the lockdown

During lockdown, message sending is disabled for all users, but they can still read messages.

## Configuration

Edit the `config.py` file to customize:
- Available self-assignable roles
- Welcome/goodbye message format
- Command prefix
- Permission levels
