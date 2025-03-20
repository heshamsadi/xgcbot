import discord
from discord.ext import commands, tasks
import aiohttp
import json
import os
import datetime
import asyncio
from typing import Dict, List, Optional
import config
import traceback

class YouTubeNotifications(commands.Cog):
    """Track YouTube channels and post notifications when new videos are uploaded"""

    def __init__(self, bot):
        self.bot = bot
        self.config_file = "youtube_config.json"
        self.config = self.load_config()
        # Only start the background task if an API key is set
        if self.config.get("api_key"):
            self.check_uploads.start()
    
    def load_config(self) -> Dict:
        """Load YouTube configuration from file or create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading YouTube config file: {e}")
                return self.get_default_config()
        else:
            default_config = self.get_default_config()
            self.save_config(default_config)
            return default_config
    
    def get_default_config(self) -> Dict:
        """Return default YouTube configuration"""
        return {
            "api_key": "",
            "check_interval": 10,  # minutes
            "channels": {},  # youtube_channel_id -> {name, last_video_id, discord_channel_id}
        }
    
    def save_config(self, config: Optional[Dict] = None) -> None:
        """Save YouTube configuration to file"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving YouTube config file: {e}")
    
    @commands.group(name="youtube", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def youtube(self, ctx):
        """YouTube notification commands"""
        embed = discord.Embed(
            title="YouTube Notification Commands",
            description="Commands for managing YouTube channel notifications",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="Setup",
            value=(
                f"`{config.PREFIX}youtube setapikey <api_key>` - Set your YouTube API key\n"
                f"`{config.PREFIX}youtube setinterval <minutes>` - Set how often to check for new videos\n"
                f"`{config.PREFIX}youtube debug` - Test if your API key is working\n"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Channel Management",
            value=(
                f"`{config.PREFIX}youtube add <youtube_channel_id> <discord_channel>` - Add a YouTube channel to track\n"
                f"`{config.PREFIX}youtube remove <youtube_channel_id>` - Remove a YouTube channel\n"
                f"`{config.PREFIX}youtube list` - List all tracked YouTube channels\n"
                f"`{config.PREFIX}youtube test [youtube_channel_id]` - Test notifications for a channel\n"
                f"`{config.PREFIX}youtube force <youtube_channel_id>` - Force post latest video without updating tracking\n"
            ),
            inline=False
        )
        
        # Test the API key if it exists
        api_key = self.config.get("api_key", "")
        if api_key:
            valid, _ = await self.test_api_key(api_key)
            if valid:
                status = "✅ API Key Valid"
                color = discord.Color.green()
            else:
                status = "❌ API Key Invalid"
                color = discord.Color.red()
        else:
            status = "❓ Not Set"
            color = discord.Color.light_grey()
            
        embed.add_field(
            name="API Key Status",
            value=f"{status} (Use `{config.PREFIX}youtube debug` for details)",
            inline=True
        )
        
        # Show if the background task is running
        if self.check_uploads.is_running():
            task_status = "✅ Running"
        else:
            task_status = "❌ Stopped"
            
        embed.add_field(
            name="Check Interval",
            value=f"{self.config.get('check_interval', 10)} minutes\nTask: {task_status}",
            inline=True
        )
        
        embed.add_field(
            name="Tracked Channels",
            value=f"{len(self.config.get('channels', {}))} channels",
            inline=True
        )
        
        embed.set_footer(text="To get a YouTube API key, visit the Google Cloud Console")
        await ctx.send(embed=embed)
    
    @youtube.command(name="setapikey")
    @commands.has_permissions(administrator=True)
    async def set_api_key(self, ctx, api_key: str):
        """Set your YouTube API key"""
        # Delete the command message to keep the API key private
        try:
            await ctx.message.delete()
        except:
            pass
        
        # Verify the API key by making a test request
        test_msg = await ctx.send("🔄 Testing API key... Please wait...")
        valid, error = await self.test_api_key(api_key)
        
        if valid:
            # Save the API key if valid
            old_key = self.config.get("api_key", "")
            self.config["api_key"] = api_key
            self.save_config()
            
            await test_msg.edit(content="✅ YouTube API key is valid and has been saved!")
            
            # Start the check task if it's not running
            if not self.check_uploads.is_running():
                self.check_uploads.start()
            
            # Send success message
            try:
                await ctx.author.send("✅ YouTube API key has been set successfully!")
            except discord.Forbidden:
                await ctx.send("✅ YouTube API key has been set successfully! (I couldn't DM you)")
        else:
            # Show the error message if key is invalid
            await test_msg.edit(content=f"❌ Invalid API key: {error}")
    
    @youtube.command(name="debug")
    @commands.has_permissions(administrator=True)
    async def debug_api(self, ctx):
        """Test if your YouTube API key is working"""
        api_key = self.config.get("api_key", "")
        
        if not api_key:
            await ctx.send("❌ No API key set. Use `!youtube setapikey` to set one.")
            return
        
        debug_msg = await ctx.send("🔄 Testing YouTube API key... Please wait...")
        
        # Make a test request to the API
        valid, error = await self.test_api_key(api_key)
        
        if valid:
            # Test passed
            embed = discord.Embed(
                title="YouTube API Key Check",
                description="✅ Your API key is working correctly!",
                color=discord.Color.green()
            )
            
            # Try to get analytics about usage
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true&key={api_key}"
                    
                    async with session.get(url) as response:
                        status = response.status
                        response_text = f"{status} ({response.reason})"
                        
                        # If status is not 200, mark as an issue
                        if status != 200:
                            embed.title = "YouTube API Key Issue"
                            embed.description = "⚠️ Your API key works for basic requests but has some limitations"
                            embed.color = discord.Color.gold()
                        
                        embed.add_field(
                            name="API Response Code",
                            value=response_text,
                            inline=False
                        )
                        
                        # Add explanation for common status codes
                        if status == 401:
                            embed.add_field(
                                name="What this means",
                                value="Your API key is not authorized for this specific request. This is normal if you didn't set up OAuth2 credentials.",
                                inline=False
                            )
            except Exception as e:
                embed.add_field(
                    name="Connection Test",
                    value=f"✅ Basic connectivity works, but additional tests failed:\n{str(e)}",
                    inline=False
                )
            
            await debug_msg.edit(content=None, embed=embed)
        else:
            # Test failed
            embed = discord.Embed(
                title="YouTube API Key Issue",
                description=f"❌ Your API key is not working correctly.",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="Error",
                value=error,
                inline=False
            )
            
            embed.add_field(
                name="Troubleshooting Steps",
                value=(
                    "1. Check if the API key is copied correctly\n"
                    "2. Make sure the YouTube Data API v3 is enabled\n"
                    "3. Check if your API key has restrictions that are too strict\n"
                    "4. Verify your API key hasn't reached quota limits\n"
                    "5. Try creating a new API key"
                ),
                inline=False
            )
            
            await debug_msg.edit(content=None, embed=embed)
    
    @youtube.command(name="setinterval")
    @commands.has_permissions(administrator=True)
    async def set_interval(self, ctx, minutes: int):
        """Set how often to check for new videos (in minutes)"""
        if minutes < 5:
            await ctx.send("⚠️ Setting the interval too low may exceed YouTube API quotas. Minimum is 5 minutes.")
            minutes = 5
        
        self.config["check_interval"] = minutes
        self.save_config()
        
        # Restart the task with the new interval
        if self.check_uploads.is_running():
            self.check_uploads.cancel()
        
        self.check_uploads.change_interval(minutes=minutes)
        
        if self.config.get("api_key"):
            self.check_uploads.start()
            await ctx.send(f"✅ YouTube check interval set to {minutes} minutes and background task restarted.")
        else:
            await ctx.send(f"✅ YouTube check interval set to {minutes} minutes, but background task not started (no API key).")
    
    @youtube.command(name="add")
    @commands.has_permissions(administrator=True)
    async def add_channel(self, ctx, youtube_channel_id: str, discord_channel: discord.TextChannel):
        """Add a YouTube channel to track"""
        api_key = self.config.get("api_key", "")
        
        if not api_key:
            await ctx.send("❌ YouTube API key not set. Please set one with `!youtube setapikey <key>`.")
            return
        
        # Validate the YouTube channel ID before adding
        status_msg = await ctx.send(f"🔍 Validating YouTube channel ID `{youtube_channel_id}`...")
        
        is_valid, result = await self.validate_youtube_channel(youtube_channel_id)
        
        if not is_valid:
            # If there's an error message, display it
            error_msg = f"❌ Invalid YouTube channel ID: `{youtube_channel_id}`"
            if isinstance(result, dict) and "error" in result:
                error_msg += f"\nError: {result['error']}"
                
                # If it's an API error, provide more details
                if "API Error" in result["error"]:
                    error_msg += "\n\nThis could mean your API key is invalid or has reached its quota limits."
                    error_msg += "\nTry running `!youtube debug` to check your API key status."
            
            await status_msg.edit(content=error_msg)
            return
        
        # Result now has channel info
        channel_info = result
        
        # Add the channel to our config
        self.config["channels"][youtube_channel_id] = {
            "name": channel_info["title"],
            "last_video_id": None,
            "discord_channel_id": discord_channel.id
        }
        self.save_config()
        
        # Update with latest video information
        latest_video = await self.get_latest_video(youtube_channel_id)
        if latest_video:
            self.config["channels"][youtube_channel_id]["last_video_id"] = latest_video["id"]["videoId"]
            self.save_config()
            
            thumbnail_url = latest_video["snippet"]["thumbnails"]["high"]["url"]
            
            embed = discord.Embed(
                title="YouTube Channel Added",
                description=f"Now tracking: **{channel_info['title']}**",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="Channel ID",
                value=f"`{youtube_channel_id}`",
                inline=True
            )
            
            embed.add_field(
                name="Latest Video",
                value=f"[{latest_video['snippet']['title']}](https://www.youtube.com/watch?v={latest_video['id']['videoId']})",
                inline=False
            )
            
            embed.add_field(
                name="Notifications",
                value=f"New uploads will be posted to {discord_channel.mention}",
                inline=False
            )
            
            embed.set_thumbnail(url=thumbnail_url)
            
            await status_msg.edit(content=None, embed=embed)
        else:
            await status_msg.edit(content=f"✅ Added YouTube channel: **{channel_info['title']}**\nNo videos found or unable to retrieve videos.\nNotifications will be sent to {discord_channel.mention}")
    
    @youtube.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def remove_channel(self, ctx, youtube_channel_id: str):
        """Remove a YouTube channel from tracking"""
        if youtube_channel_id in self.config["channels"]:
            channel_name = self.config["channels"][youtube_channel_id]["name"]
            del self.config["channels"][youtube_channel_id]
            self.save_config()
            await ctx.send(f"✅ Removed YouTube channel: **{channel_name}** (`{youtube_channel_id}`)")
        else:
            await ctx.send(f"❌ YouTube channel ID not found: `{youtube_channel_id}`")
    
    @youtube.command(name="list")
    @commands.has_permissions(administrator=True)
    async def list_channels(self, ctx):
        """List all tracked YouTube channels"""
        if not self.config["channels"]:
            await ctx.send("No YouTube channels are currently being tracked.")
            return
        
        embed = discord.Embed(
            title="Tracked YouTube Channels",
            description=f"Checking for new videos every {self.config['check_interval']} minutes",
            color=discord.Color.red()
        )
        
        for youtube_id, channel_info in self.config["channels"].items():
            discord_channel = self.bot.get_channel(channel_info["discord_channel_id"])
            channel_text = f"**{channel_info['name']}**\n"
            channel_text += f"Channel ID: `{youtube_id}`\n"
            channel_text += f"Notifications: {discord_channel.mention if discord_channel else 'Unknown channel'}"
            
            embed.add_field(
                name=channel_info["name"],
                value=channel_text,
                inline=False
            )
        
        embed.set_footer(text=f"API Status: {'✅ Active' if self.config.get('api_key') else '❌ No API key'}")
        await ctx.send(embed=embed)
    
    @youtube.command(name="test")
    @commands.has_permissions(administrator=True)
    async def test_notification(self, ctx, youtube_channel_id: str = None):
        """Test notifications for a channel or test the API directly"""
        api_key = self.config.get("api_key", "")
        
        if not api_key:
            await ctx.send("❌ YouTube API key not set. Please set one with `!youtube setapikey <key>`.")
            return
        
        # If no channel ID is specified, test the API directly with a popular channel
        if not youtube_channel_id:
            status_msg = await ctx.send("🔄 Testing API with a popular YouTube channel (T-Series)...")
            test_channel_id = "UCq-Fj5jknLsUf-MWSy4_brA"  # T-Series channel ID
            
            is_valid, result = await self.validate_youtube_channel(test_channel_id)
            
            if is_valid:
                latest_video = await self.get_latest_video(test_channel_id)
                if latest_video:
                    embed = await self.create_video_embed(latest_video)
                    await status_msg.edit(
                        content=f"✅ API test successful! Found channel: **{result['title']}**\n"
                                f"Here's what a notification will look like:",
                        embed=embed
                    )
                else:
                    await status_msg.edit(
                        content=f"⚠️ Partial success: Found channel **{result['title']}**, "
                                f"but couldn't fetch latest video. This might indicate API quota issues."
                    )
            else:
                error = result.get('error', 'Unknown error')
                await status_msg.edit(content=f"❌ API test failed: {error}")
            return
        
        # If a channel ID is specified but not in our tracking list, try to validate it first
        if youtube_channel_id not in self.config["channels"]:
            status_msg = await ctx.send(f"🔍 Channel ID `{youtube_channel_id}` not in tracked list. Validating...")
            
            is_valid, result = await self.validate_youtube_channel(youtube_channel_id)
            
            if not is_valid:
                error = result.get('error', 'Unknown error')
                await status_msg.edit(content=f"❌ YouTube channel ID not found: `{youtube_channel_id}`\nError: {error}")
                return
            
            await status_msg.edit(content=f"✅ Channel validated: {result['title']}\n🔍 Getting latest video...")
            
            latest_video = await self.get_latest_video(youtube_channel_id)
            if not latest_video:
                await status_msg.edit(content="❌ Could not fetch latest video for this channel.")
                return
            
            # Create and send notification
            embed = await self.create_video_embed(latest_video)
            
            await status_msg.edit(content=f"✅ Test successful for channel: {result['title']}", embed=embed)
            return
        
        # Normal flow for a tracked channel
        status_msg = await ctx.send(f"🔍 Getting latest video from channel...")
        
        latest_video = await self.get_latest_video(youtube_channel_id)
        if not latest_video:
            await status_msg.edit(content="❌ Could not fetch latest video for this channel.")
            return
        
        channel_info = self.config["channels"][youtube_channel_id]
        discord_channel = self.bot.get_channel(channel_info["discord_channel_id"])
        
        if not discord_channel:
            await status_msg.edit(content="❌ Discord channel not found. Please reset the destination channel.")
            return
        
        # Create and send notification
        embed = await self.create_video_embed(latest_video)
        
        # Send the test message to the current channel instead of the configured notification channel
        await status_msg.edit(
            content=f"✅ Test notification for channel **{channel_info['name']}**\nVideo: **{latest_video['snippet']['title']}**\n\nThis would be posted to {discord_channel.mention} and would look like:",
            embed=embed
        )
        
        # Also send an example of what the message would look like
        await ctx.send(
            f"🔔 **New Video Alert!** 🔔\n📺 **{latest_video['snippet']['channelTitle']}** just uploaded a new video!\n👉 **Click the title in the embed below to watch!** 👈"
        )
    
    @youtube.command(name="force")
    @commands.has_permissions(administrator=True)
    async def force_notification(self, ctx, youtube_channel_id: str):
        """Force post the latest video from a tracked channel without updating tracking status"""
        api_key = self.config.get("api_key", "")
        
        if not api_key:
            await ctx.send("❌ YouTube API key not set. Please set one with `!youtube setapikey <key>`.")
            return
        
        # Check if the channel is being tracked
        if youtube_channel_id not in self.config["channels"]:
            await ctx.send(f"❌ Channel ID `{youtube_channel_id}` is not in your tracking list. Add it first with `!youtube add`.")
            return
        
        status_msg = await ctx.send(f"🔍 Getting latest video from channel...")
        
        # Get channel info
        channel_info = self.config["channels"][youtube_channel_id]
        discord_channel = self.bot.get_channel(channel_info["discord_channel_id"])
        
        if not discord_channel:
            await status_msg.edit(content="❌ Discord channel not found. Please reset the destination channel.")
            return
        
        # Get latest video
        latest_video = await self.get_latest_video(youtube_channel_id)
        if not latest_video:
            await status_msg.edit(content="❌ Could not fetch latest video for this channel.")
            return
        
        video_id = latest_video["id"]["videoId"]
        
        # Create and send notification
        embed = await self.create_video_embed(latest_video)
        
        await discord_channel.send(
            f"🔥 **Featured Video!** 🔥\n📺 **{latest_video['snippet']['channelTitle']}** has an awesome video you should watch!\n👉 **Click the title in the embed below to watch on YouTube!** 👈",
            embed=embed
        )
        
        await status_msg.edit(content=f"✅ Latest video notification sent to {discord_channel.mention}\nChannel: {channel_info['name']}\nVideo: {latest_video['snippet']['title']}")
    
    async def test_api_key(self, api_key: str) -> tuple:
        """Test if an API key is valid by making a simple request"""
        if not api_key:
            return False, "No API key provided"
        
        try:
            async with aiohttp.ClientSession() as session:
                # Use a simple request that consumes minimal quota
                url = f"https://www.googleapis.com/youtube/v3/videos?part=id&chart=mostPopular&maxResults=1&key={api_key}"
                
                async with session.get(url) as response:
                    if response.status != 200:
                        data = await response.json()
                        error_message = data.get("error", {}).get("message", f"HTTP {response.status}")
                        error_reason = data.get("error", {}).get("errors", [{}])[0].get("reason", "unknown")
                        
                        if response.status == 400:
                            # Likely an invalid API key format
                            return False, f"API Error: {error_message}"
                        elif response.status == 403:
                            # API key not authorized for YouTube Data API
                            if "API key not valid" in error_message:
                                return False, f"Invalid API Key: {error_message}"
                            else:
                                return False, f"API Error: {error_message} (YouTube Data API might not be enabled)"
                        elif response.status == 401:
                            # Authentication issues
                            if error_reason == "keyInvalid":
                                return False, f"Invalid API Key: The API key {api_key[:5]}... is not valid"
                            else:
                                return False, f"Authentication Error: {error_message}"
                        else:
                            return False, f"API Error: HTTP {response.status} ({response.reason})"
                    
                    data = await response.json()
                    
                    if "items" in data:
                        return True, "API key is valid"
                    else:
                        return False, "API returned unexpected response format"
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    async def validate_youtube_channel(self, channel_id: str) -> tuple:
        """Validate if a YouTube channel ID exists and return channel info"""
        api_key = self.config.get("api_key", "")
        
        if not api_key:
            return False, {"error": "YouTube API key not set"}
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet&id={channel_id}&key={api_key}"
                
                async with session.get(url) as response:
                    if response.status != 200:
                        data = await response.json()
                        error_message = data.get("error", {}).get("message", f"HTTP {response.status}")
                        return False, {"error": f"API Error: {error_message}"}
                    
                    data = await response.json()
                    
                    if not data.get("items"):
                        return False, {"error": "Channel not found"}
                    
                    channel_info = {
                        "title": data["items"][0]["snippet"]["title"],
                        "thumbnail": data["items"][0]["snippet"]["thumbnails"]["default"]["url"]
                    }
                    
                    return True, channel_info
        except Exception as e:
            traceback_str = traceback.format_exc()
            print(f"Error validating YouTube channel:\n{traceback_str}")
            return False, {"error": str(e)}
    
    async def get_latest_video(self, channel_id: str) -> Optional[Dict]:
        """Get the latest video from a YouTube channel"""
        api_key = self.config.get("api_key", "")
        
        if not api_key:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://www.googleapis.com/youtube/v3/search?key={api_key}&channelId={channel_id}&part=snippet,id&order=date&maxResults=1&type=video"
                
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"YouTube API error: HTTP {response.status}")
                        try:
                            error_data = await response.json()
                            print(f"Error details: {error_data}")
                        except:
                            print(f"Could not parse error response")
                        return None
                    
                    data = await response.json()
                    
                    if not data.get("items"):
                        return None
                    
                    return data["items"][0]
        except Exception as e:
            traceback_str = traceback.format_exc()
            print(f"Error getting latest video:\n{traceback_str}")
            return None
    
    async def create_video_embed(self, video_item: Dict) -> discord.Embed:
        """Create an embed for a YouTube video"""
        video_id = video_item["id"]["videoId"]
        snippet = video_item["snippet"]
        
        # Create the embed
        embed = discord.Embed(
            title=f"🎬 {snippet['title']}",
            url=f"https://www.youtube.com/watch?v={video_id}",
            description=f"{snippet['description'][:200] + '...' if len(snippet['description']) > 200 else snippet['description']}\n\n**👆 Click the title above to watch this video on YouTube! 👆**",
            color=discord.Color.red(),
            timestamp=datetime.datetime.fromisoformat(snippet["publishedAt"].replace('Z', '+00:00'))
        )
        
        # Add thumbnail
        if "high" in snippet["thumbnails"]:
            embed.set_image(url=snippet["thumbnails"]["high"]["url"])
        
        # Add channel info
        embed.set_author(
            name=snippet["channelTitle"],
            url=f"https://www.youtube.com/channel/{snippet['channelId']}"
        )
        
        embed.set_footer(text=f"Published on YouTube • Click the title to watch")
        
        return embed
    
    @tasks.loop(minutes=10)
    async def check_uploads(self):
        """Check for new uploads from all tracked YouTube channels"""
        if not self.config.get("api_key") or not self.config.get("channels"):
            return
        
        print(f"[{datetime.datetime.now()}] Checking for YouTube uploads...")
        
        for channel_id, channel_info in self.config["channels"].items():
            try:
                # Add a delay between requests to avoid rate limiting
                await asyncio.sleep(1)
                
                latest_video = await self.get_latest_video(channel_id)
                if not latest_video:
                    print(f"No videos found or error for channel: {channel_info['name']}")
                    continue
                
                video_id = latest_video["id"]["videoId"]
                last_known_id = channel_info.get("last_video_id")
                
                # Skip if we've already seen this video or if this is the first check
                if last_known_id == video_id:
                    continue
                
                # For first-time checks, just record the video ID without posting
                if last_known_id is None:
                    print(f"First check for {channel_info['name']}, recording latest video: {video_id}")
                    self.config["channels"][channel_id]["last_video_id"] = video_id
                    self.save_config()
                    continue
                
                print(f"New video found for {channel_info['name']}: {video_id}")
                
                # Update the last known video ID
                self.config["channels"][channel_id]["last_video_id"] = video_id
                self.save_config()
                
                # Get the Discord channel to post to
                discord_channel = self.bot.get_channel(channel_info["discord_channel_id"])
                if not discord_channel:
                    print(f"Discord channel not found for {channel_info['name']}")
                    continue
                
                # Create and send notification
                embed = await self.create_video_embed(latest_video)
                
                await discord_channel.send(
                    f"🚨 **New Content Alert!** 🚨\n📺 **{latest_video['snippet']['channelTitle']}** just dropped a fresh video!\n👀 **Click the video title in the embed below to watch on YouTube!** 💯",
                    embed=embed
                )
            except Exception as e:
                traceback_str = traceback.format_exc()
                print(f"Error checking for uploads for {channel_id}:\n{traceback_str}")
    
    @check_uploads.before_loop
    async def before_check_uploads(self):
        """Wait until the bot is ready before starting the loop"""
        await self.bot.wait_until_ready()
    
    def cog_unload(self):
        """Stop the background task when the cog is unloaded"""
        if self.check_uploads.is_running():
            self.check_uploads.cancel()

async def setup(bot):
    await bot.add_cog(YouTubeNotifications(bot)) 