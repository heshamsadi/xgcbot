import discord
from discord.ext import commands
import config
from datetime import datetime
import platform
import psutil
import os

class Utilities(commands.Cog):
    """Utility commands for the bot."""

    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.utcnow()

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Check the bot's latency."""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! Latency: {latency}ms")

    @commands.command(name="info")
    async def server_info(self, ctx):
        """Display information about the server."""
        guild = ctx.guild
        
        # Get member counts
        total_members = guild.member_count
        bot_count = sum(1 for member in guild.members if member.bot)
        human_count = total_members - bot_count
        
        # Get channel counts
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        # Get role count
        role_count = len(guild.roles) - 1  # Subtract @everyone role
        
        # Create embed
        embed = discord.Embed(
            title=f"{guild.name} Information",
            description=guild.description or "No description",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Add server icon if available
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Add fields
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
        
        embed.add_field(name="Members", value=f"Total: {total_members}\nHumans: {human_count}\nBots: {bot_count}", inline=True)
        embed.add_field(name="Channels", value=f"Text: {text_channels}\nVoice: {voice_channels}\nCategories: {categories}", inline=True)
        embed.add_field(name="Roles", value=role_count, inline=True)
        
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        
        await ctx.send(embed=embed)

    @commands.command(name="botinfo")
    async def show_bot_info(self, ctx):
        """Display information about the bot."""
        # Calculate uptime
        uptime = datetime.utcnow() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{days}d, {hours}h, {minutes}m, {seconds}s"
        
        # Get system info
        try:
            # Get CPU and memory usage
            cpu_usage = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            memory_used = memory.used / (1024 ** 2)  # Convert to MB
            memory_total = memory.total / (1024 ** 2)  # Convert to MB
            
            system_info = (
                f"CPU: {cpu_usage}%\n"
                f"Memory: {memory_used:.2f}MB / {memory_total:.2f}MB\n"
                f"Python: {platform.python_version()}\n"
                f"Discord.py: {discord.__version__}"
            )
        except:
            system_info = (
                f"Python: {platform.python_version()}\n"
                f"Discord.py: {discord.__version__}"
            )
        
        # Create embed
        embed = discord.Embed(
            title=f"{self.bot.user.name} Information",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Add bot avatar if available
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        # Add fields
        embed.add_field(name="Bot ID", value=self.bot.user.id, inline=True)
        embed.add_field(name="Uptime", value=uptime_str, inline=True)
        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        
        embed.add_field(name="System Info", value=system_info, inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        
        await ctx.send(embed=embed)

    @commands.command(name="crypto")
    async def crypto_disclaimer(self, ctx):
        """Display crypto disclaimer."""
        embed = discord.Embed(
            title="Crypto Disclaimer",
            description=(
                "**Important Information for Our Community:**\n\n"
                "This server and its members do not provide financial advice. All information shared here is for educational "
                "and entertainment purposes only. Always do your own research (DYOR) before investing in any cryptocurrency.\n\n"
                "Cryptocurrency investments are volatile and carry high risk. Never invest more than you can afford to lose."
            ),
            color=discord.Color.gold()
        )
        
        await ctx.send(embed=embed)

    @commands.command(name="welcome")
    @commands.has_permissions(administrator=True)
    async def manual_welcome(self, ctx, member: discord.Member):
        """Manually send the welcome message for a member."""
        if config.WELCOME_CHANNEL_ID:
            welcome_channel = self.bot.get_channel(config.WELCOME_CHANNEL_ID)
            if welcome_channel:
                # Get member stats
                guild = member.guild
                total_members = len(guild.members)
                online_members = sum(1 for m in guild.members if m.status != discord.Status.offline)
                join_date = member.joined_at.strftime("%B %d, %Y") if member.joined_at else datetime.utcnow().strftime("%B %d, %Y")
                
                welcome_msg = config.WELCOME_MESSAGE.format(
                    member_mention=member.mention,
                    verification_channel=config.VERIFICATION_CHANNEL_ID,
                    rules_channel=config.RULES_CHANNEL_ID,
                    roles_channel=config.ROLES_CHANNEL_ID,
                    total_members=total_members,
                    online_members=online_members,
                    join_date=join_date
                )
                await welcome_channel.send(welcome_msg)
                await ctx.send(f"✅ Welcome message sent for {member.display_name} in <#{config.WELCOME_CHANNEL_ID}>")
            else:
                await ctx.send("❌ Welcome channel not found. Please check your configuration.")
        else:
            await ctx.send("❌ Welcome channel ID not configured. Please set WELCOME_CHANNEL_ID in your .env file.")

    @commands.command(name="send_verify_message")
    @commands.has_permissions(administrator=True)
    async def send_verify_message(self, ctx):
        """Sends a verification message to the alpha verification channel."""
        alpha_verify_channel_id = 1346516440945004564
        alpha_verify_channel = self.bot.get_channel(alpha_verify_channel_id)
        
        if not alpha_verify_channel:
            return await ctx.send(f"❌ Alpha verification channel not found. ID: {alpha_verify_channel_id}")
        
        embed = discord.Embed(
            title="🔐 XGC Alpha Access Verification",
            description="**Access to premium alpha channels requires verification of your NFT holdings.**",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="How to Verify",
            value="Use the `!verify` command to verify ownership of your NFTs and gain access to exclusive alpha channels.",
            inline=False
        )
        
        embed.add_field(
            name="Benefits of Verification",
            value="✅ Access to exclusive alpha channels\n"
                 "✅ Early information on upcoming projects\n"
                 "✅ Direct interaction with the team\n"
                 "✅ Premium content and insights",
            inline=False
        )
        
        embed.set_footer(text="XGC Trenches XRPL | Verification System")
        
        verification_message = await alpha_verify_channel.send(embed=embed)
        await ctx.send(f"✅ Verification message sent to {alpha_verify_channel.mention}")

async def setup(bot):
    # Try to import psutil for system stats
    try:
        import psutil
    except ImportError:
        print("psutil not installed, some stats will be unavailable")
    
    await bot.add_cog(Utilities(bot))
