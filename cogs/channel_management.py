import discord
from discord.ext import commands
import asyncio
import os
from datetime import datetime, timedelta
import typing
import config

class ChannelManagement(commands.Cog):
    """Handles channel management including auto-deletion of messages in specific channels."""
    
    def __init__(self, bot):
        self.bot = bot
        self.auto_delete_channels = {}
        self.load_auto_delete_channels()
        self.bot.loop.create_task(self.initialize_protected_channels())
        self.whitelist_message_ids = set()  # Store message IDs that should not be deleted
    
    def load_auto_delete_channels(self):
        """Load auto-delete channels from config if available."""
        if hasattr(config, 'AUTO_DELETE_CHANNELS'):
            self.auto_delete_channels = config.AUTO_DELETE_CHANNELS
        else:
            # Default to verification channel if defined in env
            alpha_verify_channel_id = 1346516440945004564  # The alpha verification channel
            if alpha_verify_channel_id:
                self.auto_delete_channels[alpha_verify_channel_id] = {
                    'delete_after': 5,  # Delete after 5 seconds
                    'protected': True,   # This channel has protected announcements
                }
    
    async def initialize_protected_channels(self):
        """Initialize protected channels by identifying announcement messages."""
        await self.bot.wait_until_ready()
        
        for channel_id, settings in self.auto_delete_channels.items():
            if settings.get('protected', False):
                channel = self.bot.get_channel(channel_id)
                if channel:
                    # Find the most recent embed from the bot as the announcement
                    async for message in channel.history(limit=30):
                        if message.author.id == self.bot.user.id and message.embeds:
                            # Found a bot message with embed, likely the announcement
                            self.whitelist_message_ids.add(message.id)
                            break
    
    @commands.command(name="clean_verify_channel")
    @commands.has_permissions(administrator=True)
    async def clean_verify_channel(self, ctx, channel: discord.TextChannel = None):
        """Clean all messages in the verification channel except bot announcements."""
        if channel is None:
            # Default to alpha verification channel
            channel_id = 1346516440945004564
            channel = self.bot.get_channel(channel_id)
        
        if not channel:
            return await ctx.send("❌ Specified channel not found.")
        
        # Find and protect bot announcement messages
        announcement_ids = []
        async for message in channel.history(limit=30):
            if message.author.id == self.bot.user.id and message.embeds:
                announcement_ids.append(message.id)
                self.whitelist_message_ids.add(message.id)
        
        # Delete all other messages
        deleted_count = 0
        async for message in channel.history(limit=100):
            if message.id not in announcement_ids:
                try:
                    await message.delete()
                    deleted_count += 1
                    # Add a small delay to avoid hitting rate limits
                    await asyncio.sleep(0.5)
                except discord.errors.NotFound:
                    pass
                except discord.errors.Forbidden:
                    await ctx.send("❌ I don't have permission to delete messages in that channel.")
                    return
        
        await ctx.send(f"✅ Cleaned verification channel. Deleted {deleted_count} messages, preserved {len(announcement_ids)} announcements.")
    
    @commands.command(name="set_auto_delete")
    @commands.has_permissions(administrator=True)
    async def set_auto_delete(self, ctx, channel: discord.TextChannel, seconds: int):
        """Set a channel to automatically delete messages after the specified seconds."""
        if seconds < 1:
            return await ctx.send("❌ Delete time must be at least 1 second.")
        
        self.auto_delete_channels[channel.id] = {
            'delete_after': seconds,
            'protected': True,
        }
        
        # Clean the channel first
        await self.clean_verify_channel(ctx, channel)
        
        await ctx.send(f"✅ Channel {channel.mention} set to auto-delete messages after {seconds} seconds, except bot announcements.")
    
    @commands.command(name="protect_message")
    @commands.has_permissions(administrator=True)
    async def protect_message(self, ctx, message_id: int, channel: discord.TextChannel = None):
        """Protect a specific message from auto-deletion."""
        if channel is None:
            channel = ctx.channel
        
        try:
            message = await channel.fetch_message(message_id)
            self.whitelist_message_ids.add(message.id)
            await ctx.send(f"✅ Message ID {message_id} is now protected from auto-deletion.")
        except discord.NotFound:
            await ctx.send(f"❌ Message with ID {message_id} not found in this channel.")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Delete messages in auto-delete channels after a delay if not from the bot."""
        # Ignore messages from bots (including our own)
        if message.author.bot:
            return
        
        # Check if channel is set for auto-deletion
        if message.channel.id in self.auto_delete_channels:
            settings = self.auto_delete_channels[message.channel.id]
            delete_after = settings.get('delete_after', 5)  # Default to 5 seconds
            
            # Store the message ID to check later
            message_id = message.id
            channel_id = message.channel.id
            
            # Schedule deletion
            await asyncio.sleep(delete_after)
            
            try:
                # Try to fetch the message to see if it still exists
                try:
                    channel = self.bot.get_channel(channel_id)
                    message = await channel.fetch_message(message_id)
                    
                    # If we got here, the message still exists and is not in whitelist
                    if message_id not in self.whitelist_message_ids:
                        await message.delete()
                except discord.NotFound:
                    # Message already deleted by another bot or user
                    pass
                except discord.HTTPException:
                    # API error, just ignore
                    pass
            except Exception as e:
                # Catch all other exceptions to prevent the bot from crashing
                print(f"Error in auto-delete: {str(e)}")

async def setup(bot):
    await bot.add_cog(ChannelManagement(bot))
