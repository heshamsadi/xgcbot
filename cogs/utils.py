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

async def setup(bot):
    # Try to import psutil for system stats
    try:
        import psutil
    except ImportError:
        print("psutil not installed, some stats will be unavailable")
    
    await bot.add_cog(Utilities(bot))
