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

## Configuration

Edit the `config.py` file to customize:
- Available self-assignable roles
- Welcome/goodbye message format
- Command prefix
- Permission levels
