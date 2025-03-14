import discord
from discord.ext import commands
import config

class Verification(commands.Cog):
    """Commands for handling user verification."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Set up verification message if it doesn't exist."""
        # Skip if verification channel or message IDs are not set
        if not config.VERIFICATION_CHANNEL_ID or not config.VERIFICATION_MESSAGE_ID:
            return
        
        # Get the verification channel
        channel = self.bot.get_channel(config.VERIFICATION_CHANNEL_ID)
        if not channel:
            return
        
        # Check if verification message exists
        try:
            # Try to fetch the message
            await channel.fetch_message(config.VERIFICATION_MESSAGE_ID)
        except discord.NotFound:
            # Message doesn't exist, create a new one
            embed = discord.Embed(
                title="Server Verification",
                description=(
                    "Welcome to the XGC Trenches XRPL! 🚀\n\n"
                    "To get verified and access all channels, please react with ✅ to this message.\n\n"
                    "Once verified, you'll receive the Verified role and gain access to all community channels."
                ),
                color=discord.Color.green()
            )
            verification_msg = await channel.send(embed=embed)
            await verification_msg.add_reaction("✅")
            
            # Log that a new verification message was created
            print(f"Created new verification message with ID: {verification_msg.id}")
            print(f"Please update your .env file with: VERIFICATION_MESSAGE_ID={verification_msg.id}")
        
    @commands.command(name="setup_verification")
    @commands.has_permissions(administrator=True)
    async def setup_verification(self, ctx):
        """Create a verification message in the verification channel."""
        # Check if verification channel is set
        if not config.VERIFICATION_CHANNEL_ID:
            return await ctx.send("Verification channel ID is not set in the config.")
        
        # Get the verification channel
        channel = self.bot.get_channel(config.VERIFICATION_CHANNEL_ID)
        if not channel:
            return await ctx.send("Verification channel not found.")
        
        # Create verification embed
        embed = discord.Embed(
            title="Server Verification",
            description=(
                "Welcome to the XGC Trenches XRPL! 🚀\n\n"
                "To get verified and access all channels, please react with ✅ to this message.\n\n"
                "Once verified, you'll receive the Verified role and gain access to all community channels."
            ),
            color=discord.Color.green()
        )
        
        # Send the message and add reaction
        verification_msg = await channel.send(embed=embed)
        await verification_msg.add_reaction("✅")
        
        # Send the message ID to the command channel
        await ctx.send(
            f"Verification message created!\n"
            f"Message ID: `{verification_msg.id}`\n"
            f"Please update your .env file with: `VERIFICATION_MESSAGE_ID={verification_msg.id}`"
        )

async def setup(bot):
    await bot.add_cog(Verification(bot))
