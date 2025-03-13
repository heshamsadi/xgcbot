import discord
from discord.ext import commands
import config
import asyncio

class ServerSetup(commands.Cog):
    """Commands for server setup and permission management."""

    def __init__(self, bot):
        self.bot = bot

    # Only allow administrators to use these commands
    async def cog_check(self, ctx):
        return ctx.author.guild_permissions.administrator

    @commands.command(name="setup_permissions")
    async def setup_permissions(self, ctx):
        """Set up basic server permissions for verified/unverified roles."""
        guild = ctx.guild
        
        # Get the verified role
        verified_role = guild.get_role(config.VERIFIED_ROLE_ID)
        if not verified_role:
            return await ctx.send("Error: Verified role not found. Please check your configuration.")
        
        # Get everyone role (unverified users)
        everyone_role = guild.default_role
        
        status_msg = await ctx.send("Setting up permissions... This may take a moment.")
        
        # Counter for modified channels
        modified_count = 0
        public_count = 0
        
        # Process all channels in the server
        for channel in guild.channels:
            # Skip voice channels for now
            if isinstance(channel, discord.VoiceChannel):
                continue
                
            # Check if the channel should be public (available to everyone)
            is_public = False
            if channel.id == config.VERIFICATION_CHANNEL_ID or channel.id == config.WELCOME_CHANNEL_ID:
                is_public = True
            
            if "welcome" in channel.name.lower() or "verification" in channel.name.lower() or \
               "rules" in channel.name.lower() or "announcements" in channel.name.lower():
                is_public = True
                
            try:
                # Set permissions for verified role (can see everything)
                await channel.set_permissions(verified_role, read_messages=True, 
                                             send_messages=True, 
                                             embed_links=True,
                                             attach_files=True,
                                             read_message_history=True)
                
                # Set permissions for unverified users
                if is_public:
                    # Public channels - everyone can see
                    await channel.set_permissions(everyone_role, read_messages=True,
                                                read_message_history=True)
                    public_count += 1
                else:
                    # Private channels - only verified users can see
                    await channel.set_permissions(everyone_role, read_messages=False)
                
                modified_count += 1
                
                # Add a short delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except discord.Forbidden:
                await ctx.send(f"Error: I don't have permission to modify channel {channel.name}.")
            except Exception as e:
                await ctx.send(f"Error setting permissions for {channel.name}: {str(e)}")
        
        await status_msg.edit(content=f"✅ Permission setup complete!\n"
                                      f"• Modified permissions for {modified_count} channels\n"
                                      f"• {public_count} public channels (visible to everyone)\n"
                                      f"• {modified_count - public_count} members-only channels (visible to verified users)")

    @commands.command(name="create_category")
    async def create_category(self, ctx, *, name):
        """Create a new category with proper permissions for verified users."""
        guild = ctx.guild
        
        # Get the verified role
        verified_role = guild.get_role(config.VERIFIED_ROLE_ID)
        if not verified_role:
            return await ctx.send("Error: Verified role not found. Please check your configuration.")
        
        # Get everyone role (unverified users)
        everyone_role = guild.default_role
        
        # Set permissions
        overwrites = {
            verified_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            everyone_role: discord.PermissionOverwrite(read_messages=False)
        }
        
        try:
            # Create the category with the specified permissions
            category = await guild.create_category(name=name, overwrites=overwrites)
            await ctx.send(f"✅ Created category **{name}** with proper permissions.\n"
                          f"• Visible to verified users\n"
                          f"• Hidden from unverified users")
            
        except discord.Forbidden:
            await ctx.send("Error: I don't have permission to create categories.")
        except Exception as e:
            await ctx.send(f"Error creating category: {str(e)}")
    
    @commands.command(name="create_channel")
    async def create_channel(self, ctx, category_name, channel_name, public: bool = False):
        """
        Create a new text channel in a specific category.
        
        Usage: !create_channel "Category Name" "channel-name" [public]
        Add 'True' at the end to make the channel public to unverified users.
        """
        guild = ctx.guild
        
        # Find the category
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            return await ctx.send(f"Category '{category_name}' not found. Create it first with `!create_category` command.")
        
        # Get the verified role
        verified_role = guild.get_role(config.VERIFIED_ROLE_ID)
        if not verified_role:
            return await ctx.send("Error: Verified role not found. Please check your configuration.")
        
        # Get everyone role (unverified users)
        everyone_role = guild.default_role
        
        # Set permissions
        overwrites = {
            verified_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            everyone_role: discord.PermissionOverwrite(
                read_messages=public,  # True if public, False otherwise
                send_messages=public   # True if public, False otherwise
            )
        }
        
        try:
            # Create the channel with the specified permissions
            channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites
            )
            
            visibility = "public (visible to everyone)" if public else "private (visible to verified users only)"
            await ctx.send(f"✅ Created channel #{channel.name} in category '{category_name}'.\n"
                          f"• Channel is {visibility}")
            
        except discord.Forbidden:
            await ctx.send("Error: I don't have permission to create channels.")
        except Exception as e:
            await ctx.send(f"Error creating channel: {str(e)}")

    @commands.command(name="add_role_to_channels")
    async def add_role_to_channels(self, ctx, role_name, category_name=None, can_view: bool = True, can_send: bool = True):
        """
        Add a role to channels with specific permissions.
        
        Usage: !add_role_to_channels "Role Name" ["Category Name"] [can_view=True] [can_send=True]
        Leave category_name blank to apply to all channels.
        """
        guild = ctx.guild
        
        # Find the role
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            return await ctx.send(f"Role '{role_name}' not found.")
        
        status_msg = await ctx.send(f"Adding permissions for role '{role_name}'... This may take a moment.")
        
        # Counter for modified channels
        modified_count = 0
        
        # Filter channels by category if specified
        channels = []
        if category_name:
            category = discord.utils.get(guild.categories, name=category_name)
            if not category:
                return await ctx.send(f"Category '{category_name}' not found.")
            channels = category.channels
        else:
            channels = guild.text_channels
        
        # Process all channels
        for channel in channels:
            try:
                # Set permissions
                await channel.set_permissions(
                    role, 
                    read_messages=can_view,
                    send_messages=can_send
                )
                
                modified_count += 1
                
                # Add a short delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except discord.Forbidden:
                await ctx.send(f"Error: I don't have permission to modify channel {channel.name}.")
            except Exception as e:
                await ctx.send(f"Error setting permissions for {channel.name}: {str(e)}")
        
        category_text = f"in category '{category_name}'" if category_name else "across the server"
        await status_msg.edit(content=f"✅ Permission setup complete!\n"
                                     f"• Modified permissions for {modified_count} channels {category_text}\n"
                                     f"• Role '{role_name}' can {'view' if can_view else 'not view'} these channels\n"
                                     f"• Role '{role_name}' can {'send messages in' if can_send else 'not send messages in'} these channels")

    @commands.group(name="setup", invoke_without_command=True)
    async def setup(self, ctx):
        """Main setup command group."""
        await ctx.send("Please specify a setup command. Available commands:\n"
                      "• `!setup server` - Set up a basic crypto server structure\n"
                      "• `!setup permissions` - Set up channel permissions\n"
                      "• `!setup help` - Show setup help")

    @setup.command(name="server")
    async def setup_server(self, ctx):
        """Set up a basic crypto server structure with categories and channels."""
        guild = ctx.guild
        
        # Get the verified role
        verified_role = guild.get_role(config.VERIFIED_ROLE_ID)
        if not verified_role:
            return await ctx.send("Error: Verified role not found. Please check your configuration.")
        
        # Get everyone role (unverified users)
        everyone_role = guild.default_role
        
        status_msg = await ctx.send("Setting up server structure... This will take a moment.")
        
        try:
            # 1. Public category (visible to everyone)
            public_overwrites = {
                verified_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                everyone_role: discord.PermissionOverwrite(read_messages=True, send_messages=False)
            }
            
            public_category = await guild.create_category(name="• INFORMATION", overwrites=public_overwrites)
            await public_category.edit(position=0)
            
            # Create public channels
            welcome = await guild.create_text_channel(name="welcome", category=public_category)
            rules = await guild.create_text_channel(name="rules", category=public_category)
            announcements = await guild.create_text_channel(name="announcements", category=public_category)
            verification = await guild.create_text_channel(name="verification", category=public_category)
            
            # Update config with verification channel
            # (This doesn't actually modify the .env file, you'll need to do that manually)
            if verification:
                config.VERIFICATION_CHANNEL_ID = verification.id
                await ctx.send(f"⚠️ Update your .env file with: VERIFICATION_CHANNEL_ID={verification.id}")
            
            # 2. Community category (verified only)
            community_overwrites = {
                verified_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                everyone_role: discord.PermissionOverwrite(read_messages=False)
            }
            
            community_category = await guild.create_category(name="• COMMUNITY", overwrites=community_overwrites)
            
            # Create community channels
            await guild.create_text_channel(name="general", category=community_category)
            await guild.create_text_channel(name="crypto-talk", category=community_category)
            await guild.create_text_channel(name="trading", category=community_category)
            await guild.create_text_channel(name="market-analysis", category=community_category)
            
            # 3. Resources category (verified only)
            resources_category = await guild.create_category(name="• RESOURCES", overwrites=community_overwrites)
            
            await guild.create_text_channel(name="useful-links", category=resources_category)
            await guild.create_text_channel(name="tutorials", category=resources_category)
            await guild.create_text_channel(name="tools", category=resources_category)
            
            # 4. Bot category (verified only)
            bot_category = await guild.create_category(name="• BOT COMMANDS", overwrites=community_overwrites)
            
            await guild.create_text_channel(name="bot-commands", category=bot_category)
            
            await status_msg.edit(content="✅ Server setup complete! Basic crypto server structure has been created.")
            
            # Create verification message in the verification channel
            embed = discord.Embed(
                title="Server Verification",
                description=(
                    "Welcome to the XGC Crypto Server! 🚀\n\n"
                    "To get verified and access all channels, please react with ✅ to this message.\n\n"
                    "Once verified, you'll receive the Verified role and gain access to all community channels."
                ),
                color=discord.Color.green()
            )
            
            verification_msg = await verification.send(embed=embed)
            await verification_msg.add_reaction("✅")
            
            await ctx.send(f"✅ Created verification message. Update your .env file with: VERIFICATION_MESSAGE_ID={verification_msg.id}")
            
        except discord.Forbidden:
            await ctx.send("Error: I don't have permission to create categories or channels.")
        except Exception as e:
            await ctx.send(f"Error during server setup: {str(e)}")

    @setup.command(name="permissions")
    async def setup_permissions_subcommand(self, ctx):
        """Set up basic server permissions for verified/unverified roles."""
        await self.setup_permissions(ctx)

    @setup.command(name="help")
    async def setup_help(self, ctx):
        """Show help information for all setup commands."""
        embed = discord.Embed(
            title="Server Setup Commands",
            description="Commands to help you set up and manage your crypto server.",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Basic Setup",
            value=(
                f"`{config.PREFIX}setup server` - Create a basic crypto server structure\n"
                f"`{config.PREFIX}setup permissions` - Set up permissions for verified/unverified users\n"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Channel Management",
            value=(
                f"`{config.PREFIX}create_category \"Name\"` - Create a new category\n"
                f"`{config.PREFIX}create_channel \"Category\" \"channel-name\" [public]` - Create a new channel\n"
                f"`{config.PREFIX}add_role_to_channels \"Role\" [\"Category\"] [can_view] [can_send]` - Add role permissions\n"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerSetup(bot))
