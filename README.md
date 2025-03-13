# XGC Crypto Discord Bot

A Discord bot designed specifically for crypto communities with features including account verification, role management, moderation tools, and welcome/goodbye messages.

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

- `!role @user [RoleName]` - Assign a role to a user (mod only)
- `!getrole [RoleName]` - Self-assign an available role
- `!kick @user [reason]` - Kick a user (mod only)
- `!ban @user [reason]` - Ban a user (mod only)
- `!clear [number]` - Clear specified number of messages (mod only)

## Configuration

Edit the `config.py` file to customize:
- Available self-assignable roles
- Welcome/goodbye message format
- Command prefix
- Permission levels
