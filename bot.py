import discord
from discord.ext import commands
import os
import config
import asyncio
from datetime import datetime

# Set up intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

# Initialize bot with prefix and intents
bot = commands.Bot(command_prefix=config.PREFIX, intents=intents)

# Remove default help command to implement custom help
bot.remove_command('help')

# Bot events
@bot.event
async def on_ready():
    """Event triggered when the bot is ready and connected to Discord."""
    print(f'Bot connected as {bot.user.name}')
    print(f'Bot ID: {bot.user.id}')
    print(f'Discord.py version: {discord.__version__}')
    print('------')
    
    # Set bot status
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="for new members"
    ))
    
    # Load all cogs
    async def load_extensions():
        for extension in [
            "cogs.moderation", 
            "cogs.roles", 
            "cogs.utils",
            "cogs.verification",
            "cogs.server_setup"
        ]:
            try:
                await bot.load_extension(extension)
                print(f'Loaded extension: {extension}')
            except Exception as e:
                print(f'Failed to load extension {extension}: {e}')
    await load_extensions()

@bot.event
async def on_member_join(member):
    """Event triggered when a new member joins the server."""
    # Send welcome message
    if config.WELCOME_CHANNEL_ID:
        welcome_channel = bot.get_channel(config.WELCOME_CHANNEL_ID)
        if welcome_channel:
            welcome_msg = config.WELCOME_MESSAGE.format(
                member_mention=member.mention,
                verification_channel=config.VERIFICATION_CHANNEL_ID
            )
            await welcome_channel.send(welcome_msg)
    
    # Send verification DM
    try:
        verification_dm = config.VERIFICATION_DM.format(
            verification_channel=config.VERIFICATION_CHANNEL_ID
        )
        await member.send(verification_dm)
    except discord.Forbidden:
        # Cannot send DM to this user
        pass

@bot.event
async def on_member_remove(member):
    """Event triggered when a member leaves the server."""
    if config.WELCOME_CHANNEL_ID:
        welcome_channel = bot.get_channel(config.WELCOME_CHANNEL_ID)
        if welcome_channel:
            goodbye_msg = config.GOODBYE_MESSAGE.format(
                member_name=member.display_name
            )
            await welcome_channel.send(goodbye_msg)

@bot.event
async def on_raw_reaction_add(payload):
    """Event triggered when a reaction is added to a message."""
    # Skip if verification message ID is not set
    if config.VERIFICATION_MESSAGE_ID == 0:
        return
        
    # Check if reaction was added to the verification message
    if payload.message_id == config.VERIFICATION_MESSAGE_ID:
        if str(payload.emoji) == "✅":
            guild = bot.get_guild(payload.guild_id)
            if not guild:
                return
            
            member = guild.get_member(payload.user_id)
            if not member or member.bot:
                return
            
            # Add verified role
            verified_role = guild.get_role(config.VERIFIED_ROLE_ID)
            if verified_role:
                await member.add_roles(verified_role)
                try:
                    await member.send(f"You have been verified in {guild.name}! You now have access to all channels.")
                except discord.Forbidden:
                    pass

@bot.event
async def on_command_error(ctx, error):
    """Global error handler for commands."""
    if isinstance(error, commands.CommandNotFound):
        return
    
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param.name}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"Invalid argument provided.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send(f"I don't have the necessary permissions to do this.")
    else:
        # Log the error
        print(f'Error: {error}')
        await ctx.send("An error occurred while executing that command.")

# Help command
@bot.command(name="help")
async def _help(ctx):
    """Shows all available commands."""
    embed = discord.Embed(
        title="XGC Crypto Bot Help",
        description="Here are all available commands:",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    
    # General commands
    embed.add_field(
        name="General",
        value=(
            f"`{config.PREFIX}help` - Show this help message\n"
            f"`{config.PREFIX}getrole [role]` - Assign yourself a role\n"
            f"`{config.PREFIX}ping` - Check bot latency\n"
            f"`{config.PREFIX}info` - Show server information\n"
            f"`{config.PREFIX}botinfo` - Show bot information\n"
            f"`{config.PREFIX}crypto` - Display crypto disclaimer\n"
        ),
        inline=False
    )
    
    # Moderation commands
    embed.add_field(
        name="Moderation",
        value=(
            f"`{config.PREFIX}kick @user [reason]` - Kick a user from the server\n"
            f"`{config.PREFIX}ban @user [reason]` - Ban a user from the server\n"
            f"`{config.PREFIX}clear [amount]` - Clear messages from a channel\n"
        ),
        inline=False
    )
    
    # Server setup commands (admin only)
    embed.add_field(
        name="Server Setup (Admin Only)",
        value=(
            f"`{config.PREFIX}setup server` - Create a basic crypto server structure\n"
            f"`{config.PREFIX}setup permissions` - Set up permissions for roles\n"
            f"`{config.PREFIX}create_category \"Name\"` - Create a new category\n"
            f"`{config.PREFIX}create_channel \"Category\" \"channel-name\" [public]` - Create a new channel\n"
            f"`{config.PREFIX}add_role_to_channels \"Role\" [\"Category\"]` - Add role permissions\n"
        ),
        inline=False
    )
    
    embed.set_footer(text=f"Requested by {ctx.author.display_name}")
    await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    if not config.TOKEN:
        print("Error: No Discord token found in .env file")
        exit(1)
    
    asyncio.run(bot.start(config.TOKEN))
