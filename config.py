import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
PREFIX = '!'

# Discord API Token
TOKEN = os.getenv('DISCORD_TOKEN')

# Channel IDs
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID', 0))
VERIFICATION_CHANNEL_ID = int(os.getenv('VERIFICATION_CHANNEL_ID', 0))
MOD_CHANNEL_ID = int(os.getenv('MOD_CHANNEL_ID', 0))
RULES_CHANNEL_ID = int(os.getenv('RULES_CHANNEL_ID', 0))
ROLES_CHANNEL_ID = int(os.getenv('ROLES_CHANNEL_ID', 0))

# Message IDs
VERIFICATION_MESSAGE_ID = int(os.getenv('VERIFICATION_MESSAGE_ID', 0))

# Role IDs
VERIFIED_ROLE_ID = int(os.getenv('VERIFIED_ROLE_ID', 0))
MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', 0))

# Channel auto-deletion settings (channel_id: {settings})
AUTO_DELETE_CHANNELS = {
    1346516440945004564: {  # Alpha verification channel
        'delete_after': 5,  # Delete messages after 5 seconds
        'protected': True,  # Protect bot announcements
    }
}

# Self-assignable roles (role_name: role_id)
SELF_ASSIGNABLE_ROLES = {
    "trader": "Trader",
    "hodler": "HODLer",
    "analyst": "Analyst",
    "developer": "Developer",
    "investor": "Investor"
}

# Welcome message format
WELCOME_MESSAGE = """
🎉 **Welcome to XGC Trenches XRPL**, {member_mention}! 🚀

You've entered the Alpha Zone.
📜 Read the rules in <#{rules_channel}>
🎭 Grab roles in <#{roles_channel}>
✅ Get verified in <#{verification_channel}>

🌍 Total Members: {total_members}
🟢 Online Members: {online_members}
🔥 Join Date: {join_date}

*Stay ahead of the market with XGC Trenches XRPL!*
"""

# Goodbye message format
GOODBYE_MESSAGE = "**{member_name}** has left the server. 👋"

# Verification DM message
VERIFICATION_DM = """
Welcome to XGC Trenches XRPL! 🚀

To get verified and access all channels, please:
1. Go to <#{verification_channel}>
2. Find the verification message
3. React with ✅

Once verified, you'll receive the Verified role and gain access to all community channels.
"""
