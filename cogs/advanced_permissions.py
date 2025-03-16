import discord
from discord.ext import commands
import config
import asyncio
import json
import os
from typing import Optional, List, Dict, Union, Tuple
import datetime

class AdvancedPermissions(commands.Cog):
    """Advanced permission management for Discord servers."""

    def __init__(self, bot):
        self.bot = bot
        self.permissions_file = "channel_permissions.json"
        self.permissions_data = self.load_permissions()
    
    def load_permissions(self) -> Dict:
        """Load permissions data from file or create default data structure."""
        if os.path.exists(self.permissions_file):
            try:
                with open(self.permissions_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading permissions file: {e}")
                return self.get_default_permissions()
        else:
            return self.get_default_permissions()
    
    def get_default_permissions(self) -> Dict:
        """Return default permissions data structure."""
        return {
            "public_channels": [],  # Channels visible to everyone
            "role_permissions": {},  # Role-specific permission overrides
            "channel_groups": {     # Groups of channels with shared permissions
                "public": [],
                "verified_only": [],
                "moderator_only": []
            }
        }
    
    def _save_permissions_data(self):
        """Save permissions data to file."""
        try:
            with open(self.permissions_file, 'w') as f:
                json.dump(self.permissions_data, f, indent=4)
        except Exception as e:
            print(f"Error saving permissions file: {e}")
    
    async def cog_check(self, ctx):
        """Check if user has administrator permission."""
        return ctx.author.guild_permissions.administrator
    
    @commands.group(name="channels", invoke_without_command=True)
    async def channels(self, ctx):
        """Channel and permission management commands."""
        embed = discord.Embed(
            title="Channel Management Commands",
            description="Commands for managing channel permissions",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Channel Groups",
            value=(
                f"`{config.PREFIX}channels list` - List all channel groups\n"
                f"`{config.PREFIX}channels create_group <name>` - Create a new channel group\n"
                f"`{config.PREFIX}channels add_to_group <group_name> <#channel> [#channel2 ...]` - Add channels to a group\n"
                f"`{config.PREFIX}channels remove_from_group <group_name> <#channel> [#channel2 ...]` - Remove channels from a group\n"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Permission Management",
            value=(
                f"`{config.PREFIX}channels set_group_permission <group_name> <role_name> <permission> <true/false>` - Set permission for a role\n"
                f"`{config.PREFIX}channels set_permission <#channel> <role_name> <permission> <true/false>` - Set permission for a specific channel\n"
                f"`{config.PREFIX}channels apply_permissions` - Apply all permission settings\n"
                f"`{config.PREFIX}channels set_public <#channel> [#channel2 ...]` - Make channels visible to everyone\n"
                f"`{config.PREFIX}channels set_verified_only <#channel> [#channel2 ...]` - Make channels visible only to verified users\n"
                f"`{config.PREFIX}channels all_verified_only <#channel> [#channel2 ...]` - Make all channels verified-only except the specified channels\n"
                f"`{config.PREFIX}channels lockdown <mode>` - Lock down the server to prevent spam or raids\n"
                f"`{config.PREFIX}channels restrict_send --channels #channel1 #channel2 --roles \"Role1\" \"Role2\" \"Mod\"` - Restrict sending messages in channels to specific roles\n"
                f"`{config.PREFIX}channels list_restrictions` - List all channel restrictions currently set up\n"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @channels.command(name="list")
    async def list_channel_groups(self, ctx):
        """List all channel groups and their channels."""
        embed = discord.Embed(
            title="Channel Groups",
            description="Groups of channels with shared permissions",
            color=discord.Color.blue()
        )
        
        # Get the guild's channels
        guild_channels = {channel.id: channel for channel in ctx.guild.channels}
        
        # Add fields for each channel group
        for group_name, channel_ids in self.permissions_data["channel_groups"].items():
            # Get channel names from IDs
            channel_list = []
            for channel_id in channel_ids:
                channel = guild_channels.get(channel_id)
                if channel:
                    channel_list.append(f"#{channel.name}")
            
            # Format the channel list
            if channel_list:
                channels_text = "\n".join(channel_list)
            else:
                channels_text = "*No channels in this group*"
            
            embed.add_field(
                name=f"Group: {group_name}",
                value=channels_text,
                inline=False
            )
        
        # Add public channels
        public_channels = []
        for channel_id in self.permissions_data["public_channels"]:
            channel = guild_channels.get(channel_id)
            if channel:
                public_channels.append(f"#{channel.name}")
        
        if public_channels:
            public_text = "\n".join(public_channels)
        else:
            public_text = "*No public channels*"
        
        embed.add_field(
            name="Public Channels",
            value=public_text,
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @channels.command(name="create_group")
    async def create_channel_group(self, ctx, *, group_name: str):
        """Create a new channel group."""
        # Check if group already exists
        if group_name in self.permissions_data["channel_groups"]:
            return await ctx.send(f"❌ Group '{group_name}' already exists.")
        
        # Create the new group
        self.permissions_data["channel_groups"][group_name] = []
        self._save_permissions_data()
        
        await ctx.send(f"✅ Created new channel group: **{group_name}**")
    
    @channels.command(name="add_to_group")
    async def add_to_channel_group(self, ctx, group_name: str, *channels: discord.TextChannel):
        """Add channels to a group."""
        # Check if group exists
        if group_name not in self.permissions_data["channel_groups"]:
            return await ctx.send(f"❌ Group '{group_name}' doesn't exist. Create it first with `{config.PREFIX}channels create_group {group_name}`")
        
        if not channels:
            return await ctx.send("❌ Please specify at least one channel to add to the group.")
        
        # Add channels to the group
        added_channels = []
        for channel in channels:
            if channel.id not in self.permissions_data["channel_groups"][group_name]:
                self.permissions_data["channel_groups"][group_name].append(channel.id)
                added_channels.append(f"#{channel.name}")
        
        self._save_permissions_data()
        
        if added_channels:
            added_text = ", ".join(added_channels)
            await ctx.send(f"✅ Added {added_text} to group **{group_name}**")
        else:
            await ctx.send(f"ℹ️ No new channels were added to group **{group_name}**")
    
    @channels.command(name="remove_from_group")
    async def remove_from_channel_group(self, ctx, group_name: str, *channels: discord.TextChannel):
        """Remove channels from a group."""
        # Check if group exists
        if group_name not in self.permissions_data["channel_groups"]:
            return await ctx.send(f"❌ Group '{group_name}' doesn't exist.")
        
        if not channels:
            return await ctx.send("❌ Please specify at least one channel to remove from the group.")
        
        # Remove channels from the group
        removed_channels = []
        for channel in channels:
            if channel.id in self.permissions_data["channel_groups"][group_name]:
                self.permissions_data["channel_groups"][group_name].remove(channel.id)
                removed_channels.append(f"#{channel.name}")
        
        self._save_permissions_data()
        
        if removed_channels:
            removed_text = ", ".join(removed_channels)
            await ctx.send(f"✅ Removed {removed_text} from group **{group_name}**")
        else:
            await ctx.send(f"ℹ️ No channels were removed from group **{group_name}**")
    
    @channels.command(name="set_group_permission")
    async def set_group_permission(self, ctx, group_name: str, role_name: str, permission: str, value: bool):
        """Set a permission for a role in a channel group."""
        # Check if group exists
        if group_name not in self.permissions_data["channel_groups"]:
            return await ctx.send(f"❌ Group '{group_name}' doesn't exist.")
        
        # Find the role
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send(f"❌ Role '{role_name}' doesn't exist.")
        
        # Check if the permission is valid
        valid_permissions = [
            "read_messages", "send_messages", "embed_links", "attach_files", 
            "read_message_history", "mention_everyone", "add_reactions"
        ]
        
        if permission not in valid_permissions:
            valid_perms_text = ", ".join(valid_permissions)
            return await ctx.send(f"❌ Invalid permission: '{permission}'. Valid permissions are: {valid_perms_text}")
        
        # Initialize role permissions if needed
        if str(role.id) not in self.permissions_data["role_permissions"]:
            self.permissions_data["role_permissions"][str(role.id)] = {}
        
        # Initialize group permissions for this role if needed
        if "groups" not in self.permissions_data["role_permissions"][str(role.id)]:
            self.permissions_data["role_permissions"][str(role.id)]["groups"] = {}
        
        # Set the permission
        if group_name not in self.permissions_data["role_permissions"][str(role.id)]["groups"]:
            self.permissions_data["role_permissions"][str(role.id)]["groups"][group_name] = {}
        
        self.permissions_data["role_permissions"][str(role.id)]["groups"][group_name][permission] = value
        self._save_permissions_data()
        
        permission_status = "allowed" if value else "denied"
        await ctx.send(f"✅ Set permission '{permission}' to {permission_status} for role '{role_name}' in group '{group_name}'")
    
    @channels.command(name="set_permission")
    async def set_channel_permission(self, ctx, *args):
        """Set a permission for role(s) in specific channel(s).
        
        Usage: 
        - Standard: !channels set_permission #channel @role permission true/false
        - Multiple: !channels set_permission channels #channel1 #channel2 roles @role1 @role2 permission true/false
        """
        # Check for minimum arguments
        if len(args) < 3:
            return await ctx.send("❌ Not enough arguments. Usage: `!channels set_permission #channel @role permission true/false` or `!channels set_permission channels #channel1 #channel2 roles @role1 @role2 permission true/false`")
        
        # Handle both single and multiple channel/role format
        if args[0].lower() == 'channels':
            # Find where 'roles' keyword is in the arguments
            try:
                roles_index = [i for i, arg in enumerate(args) if arg.lower() == 'roles'][0]
                
                # Extract channels and roles
                channel_inputs = args[1:roles_index]
                
                # Find permission and value which should be the last two arguments
                permission = args[-2]
                value_str = args[-1]
                
                # Extract roles (between 'roles' keyword and the permission)
                role_inputs = args[roles_index+1:-2]
                
                if not channel_inputs or not role_inputs:
                    return await ctx.send("❌ Missing channels or roles arguments.")
            except (IndexError, ValueError):
                return await ctx.send("❌ Invalid format. Usage: `!channels set_permission channels #channel1 #channel2 roles @role1 @role2 permission true/false`")
        else:
            # Standard format: channel role permission value
            if len(args) != 4:
                return await ctx.send("❌ Invalid number of arguments. Usage: `!channels set_permission #channel @role permission true/false`")
            
            channel_inputs = [args[0]]
            role_inputs = [args[1]]
            permission = args[2]
            value_str = args[3]
        
        # Validate permission value
        if value_str.lower() not in ["true", "false"]:
            return await ctx.send("❌ Permission value must be 'true' or 'false'.")
        
        value = value_str.lower() == "true"
        
        # Validate the permission
        if not hasattr(discord.Permissions, permission):
            return await ctx.send(f"❌ Invalid permission: {permission}")
        
        guild = ctx.guild
        processed_channels = []
        processed_roles = []
        
        # Resolve all channels
        channels = []
        for channel_input in channel_inputs:
            channel = self._resolve_channel(guild, channel_input)
            if channel:
                channels.append(channel)
            else:
                await ctx.send(f"⚠️ Channel not found: {channel_input}")
        
        if not channels:
            return await ctx.send("❌ No valid channels specified.")
        
        # Resolve all roles
        roles = []
        for role_input in role_inputs:
            role = self._resolve_role(guild, role_input)
            if role:
                roles.append(role)
            else:
                await ctx.send(f"⚠️ Role not found: {role_input}")
        
        if not roles:
            return await ctx.send("❌ No valid roles specified.")
        
        # Update permissions for each combination of channel and role
        status_msg = await ctx.send(f"Setting permissions... This may take a moment.")
        permission_status = "allowed" if value else "denied"
        total_changes = 0
        
        for channel in channels:
            for role in roles:
                # Update the permissions data structure
                if "role_permissions" not in self.permissions_data:
                    self.permissions_data["role_permissions"] = {}
                
                if str(role.id) not in self.permissions_data["role_permissions"]:
                    self.permissions_data["role_permissions"][str(role.id)] = {"channels": {}}
                
                if "channels" not in self.permissions_data["role_permissions"][str(role.id)]:
                    self.permissions_data["role_permissions"][str(role.id)]["channels"] = {}
                
                if str(channel.id) not in self.permissions_data["role_permissions"][str(role.id)]["channels"]:
                    self.permissions_data["role_permissions"][str(role.id)]["channels"][str(channel.id)] = {}
                
                # Set the permission in our data structure
                self.permissions_data["role_permissions"][str(role.id)]["channels"][str(channel.id)][permission] = value
                
                # Now actually apply the permission to Discord
                try:
                    # Get current overwrites or create new ones
                    overwrite = channel.overwrites_for(role)
                    
                    # Set the specific permission
                    setattr(overwrite, permission, value)
                    
                    # Apply the updated overwrites
                    await channel.set_permissions(role, overwrite=overwrite)
                    
                    # Keep track of successful changes
                    if channel not in processed_channels:
                        processed_channels.append(channel)
                    if role not in processed_roles:
                        processed_roles.append(role)
                    total_changes += 1
                    
                    # Short delay to avoid rate limits
                    await asyncio.sleep(0.3)
                except discord.Forbidden:
                    await ctx.send(f"❌ Error: I don't have permission to modify channel {channel.name} for role {role.name}.")
                except Exception as e:
                    await ctx.send(f"❌ Error setting permissions for {channel.name}/{role.name}: {str(e)}")
        
        # Save the updated permissions to file
        self._save_permissions_data()
        
        if total_changes > 0:
            channels_text = ", ".join([f"{ch.name} [ID: {ch.id}]" for ch in processed_channels])
            roles_text = ", ".join([f"{r.name} [ID: {r.id}]" for r in processed_roles])
            
            await status_msg.edit(content=f"✅ Set permission '{permission}' to {permission_status} for {len(processed_roles)} role(s) in {len(processed_channels)} channel(s).")
            
            # Create an embed with details if there are many changes
            if len(processed_channels) > 3 or len(processed_roles) > 3:
                embed = discord.Embed(
                    title=f"Permission Update: '{permission}' → {permission_status}",
                    color=discord.Color.green() if value else discord.Color.red()
                )
                embed.add_field(name="Channels", value=channels_text[:1024], inline=False)
                embed.add_field(name="Roles", value=roles_text[:1024], inline=False)
                await ctx.send(embed=embed)
        else:
            await status_msg.edit(content="❌ No permissions were updated.")
    
    @channels.command(name="set_verified_only")
    async def set_verified_only(self, ctx, *channels_input):
        """Make channels visible only to verified users. Accept channel mentions, names, or IDs."""
        if not channels_input:
            return await ctx.send("❌ Please specify at least one channel.")
        
        # Initialize the verified_only group if it doesn't exist
        if "verified_only" not in self.permissions_data["channel_groups"]:
            self.permissions_data["channel_groups"]["verified_only"] = []
        
        # Process each channel input (could be a mention, name, or ID)
        added_channels = []
        guild = ctx.guild
        verified_role = guild.get_role(config.VERIFIED_ROLE_ID)
        everyone_role = guild.default_role
        
        if not verified_role:
            return await ctx.send("❌ Error: Verified role not found. Please check your configuration.")
        
        for channel_input in channels_input:
            # Use the helper method to resolve channel
            channel = self._resolve_channel(guild, channel_input)
            
            if not channel:
                await ctx.send(f"❌ Invalid argument provided: {channel_input}")
                continue
            
            # Add to verified_only group if not already in it
            if channel.id not in self.permissions_data["channel_groups"]["verified_only"]:
                self.permissions_data["channel_groups"]["verified_only"].append(channel.id)
            
            try:
                # Set permissions for verified role - can see and interact
                verified_overwrite = discord.PermissionOverwrite()
                verified_overwrite.view_channel = True
                
                if isinstance(channel, discord.VoiceChannel):
                    verified_overwrite.connect = True
                    verified_overwrite.speak = True
                    verified_overwrite.stream = True
                    verified_overwrite.use_voice_activation = True
                else:
                    verified_overwrite.read_messages = True
                    verified_overwrite.send_messages = True
                    verified_overwrite.add_reactions = True
                
                await channel.set_permissions(verified_role, overwrite=verified_overwrite)
                
                # Set permissions for everyone role - completely hidden
                if isinstance(channel, discord.VoiceChannel):
                    # Voice channels need special handling to be fully hidden
                    overwrite = discord.PermissionOverwrite()
                    overwrite.view_channel = False  # This should hide the channel
                    overwrite.connect = False
                    overwrite.speak = False
                    await channel.set_permissions(everyone_role, overwrite=overwrite)
                    
                    # A special additional step for voice channels
                    # Check if the category permissions need to be adjusted
                    if channel.category:
                        # Try to hide at the category level too for this channel
                        try:
                            # Get existing permission overwrites for this channel in the category
                            category_overwrite = channel.category.overwrites_for(everyone_role)
                            category_overwrite.update(view_channel=False)
                            await channel.category.set_permissions(everyone_role, overwrite=category_overwrite)
                            
                            # IMPORTANT: Also ensure verified role can see the category
                            verified_category_overwrite = channel.category.overwrites_for(verified_role)
                            verified_category_overwrite.update(view_channel=True)
                            await channel.category.set_permissions(verified_role, overwrite=verified_category_overwrite)
                        except Exception as e:
                            # If we can't modify category permissions, that's fine
                            await ctx.send(f"Note: Could not update category permissions: {str(e)}")
                else:
                    # Text channel permissions
                    overwrite = discord.PermissionOverwrite()
                    overwrite.view_channel = False
                    overwrite.read_messages = False
                    overwrite.send_messages = False
                    overwrite.add_reactions = False
                    await channel.set_permissions(everyone_role, overwrite=overwrite)
                
                added_channels.append(f"{channel.name} ({channel.type}) [ID: {channel.id}]")
            except discord.Forbidden:
                await ctx.send(f"❌ Error: I don't have permission to modify channel {channel.name}.")
            except Exception as e:
                await ctx.send(f"❌ Error setting permissions for {channel.name}: {str(e)}")
        
        self._save_permissions_data()
        
        if added_channels:
            added_text = ", ".join(added_channels)
            await ctx.send(f"✅ Made the following channels verified-only: {added_text}")
        else:
            await ctx.send("❌ No valid channels specified.")
    
    @channels.command(name="set_public")
    async def set_public(self, ctx, *channels_input):
        """Make channels visible to everyone. Accept channel mentions, names, or IDs."""
        if not channels_input:
            return await ctx.send("❌ Please specify at least one channel.")
        
        # Initialize the public_channels list if it doesn't exist
        if "public_channels" not in self.permissions_data:
            self.permissions_data["public_channels"] = []
        
        # Process each channel input (could be a mention, name, or ID)
        added_channels = []
        guild = ctx.guild
        everyone_role = guild.default_role
        
        for channel_input in channels_input:
            # Use the helper method to resolve channel
            channel = self._resolve_channel(guild, channel_input)
            
            if not channel:
                await ctx.send(f"❌ Invalid argument provided: {channel_input}")
                continue
            
            # Add to public_channels if not already in it
            if channel.id not in self.permissions_data["public_channels"]:
                self.permissions_data["public_channels"].append(channel.id)
            
            try:
                # Set permissions for everyone role - can see and interact
                overwrite = discord.PermissionOverwrite()
                overwrite.view_channel = True
                overwrite.connect = True if isinstance(channel, discord.VoiceChannel) else None
                overwrite.read_messages = True if isinstance(channel, discord.TextChannel) else None
                await channel.set_permissions(everyone_role, overwrite=overwrite)
                
                added_channels.append(f"{channel.name} ({channel.type}) [ID: {channel.id}]")
            except discord.Forbidden:
                await ctx.send(f"❌ Error: I don't have permission to modify channel {channel.name}.")
            except Exception as e:
                await ctx.send(f"❌ Error setting permissions for {channel.name}: {str(e)}")
        
        self._save_permissions_data()
        
        if added_channels:
            added_text = ", ".join(added_channels)
            await ctx.send(f"✅ Made the following channels public: {added_text}")
        else:
            await ctx.send("❌ No valid channels specified.")
    
    @channels.command(name="all_verified_only")
    async def set_all_verified_only(self, ctx, *channel_args):
        """Make all channels verified-only except for the specified channels (which remain public).
        
        You can specify channels by mention (#channel), name (channel-name), or ID (1234567890).
        """
        guild = ctx.guild
        
        # Resolve channel arguments (could be mentions, names, or IDs)
        exception_channels = []
        
        for arg in channel_args:
            # Try to resolve mention
            if arg.startswith('<#') and arg.endswith('>'):
                try:
                    channel_id = int(arg[2:-1])
                    channel = guild.get_channel(channel_id)
                    if channel:
                        exception_channels.append(channel)
                except (ValueError, TypeError):
                    pass
            # Check if it's an ID (all digits)
            elif arg.isdigit():
                try:
                    channel_id = int(arg)
                    channel = guild.get_channel(channel_id)
                    if channel:
                        exception_channels.append(channel)
                except (ValueError, TypeError):
                    pass
            else:
                # Try to find by name
                channel_name = arg.lstrip('#')
                channel = discord.utils.get(guild.channels, name=channel_name)
                if channel:
                    exception_channels.append(channel)
        
        # Confirm action
        confirm_msg = "⚠️ This will make ALL channels verified-only (hidden from unverified users) except for:"
        for channel in exception_channels:
            confirm_msg += f"\n- {channel.name} ({channel.type}) [ID: {channel.id}]"
        
        confirm_msg += "\n\nDo you want to continue? (yes/no)"
        await ctx.send(confirm_msg)
        
        # Wait for confirmation
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no', 'y', 'n']
        
        try:
            response = await self.bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            return await ctx.send("❌ Action cancelled due to timeout.")
        
        if response.content.lower() not in ['yes', 'y']:
            return await ctx.send("❌ Action cancelled.")
        
        # Process all channels
        status_msg = await ctx.send("Configuring channel permissions... This may take a moment.")
        
        # Clear existing public channels
        self.permissions_data["public_channels"] = [channel.id for channel in exception_channels]
        
        # Initialize or update the verified_only group
        if "verified_only" not in self.permissions_data["channel_groups"]:
            self.permissions_data["channel_groups"]["verified_only"] = []
        
        # Add all other channels to verified_only
        verified_only_channels = []
        for channel in guild.channels:
            # Skip categories and non-text/voice channels
            if isinstance(channel, discord.CategoryChannel) or not (isinstance(channel, discord.TextChannel) or isinstance(channel, discord.VoiceChannel)):
                continue
                
            # Skip channels in exception list
            if channel in exception_channels:
                continue
                
            # Add to verified_only group
            if channel.id not in self.permissions_data["channel_groups"]["verified_only"]:
                self.permissions_data["channel_groups"]["verified_only"].append(channel.id)
            
            verified_only_channels.append(channel)
        
        self._save_permissions_data()
        
        # Apply permissions
        modified_count = 0
        
        # Get the verified role
        verified_role = guild.get_role(config.VERIFIED_ROLE_ID)
        if not verified_role:
            await ctx.send("❌ Error: Verified role not found. Please check your configuration.")
            return
        
        # Get everyone role (unverified users)
        everyone_role = guild.default_role
        
        # Apply permissions for verified-only channels
        for channel in verified_only_channels:
            try:
                # Set permissions for verified role - can see
                if isinstance(channel, discord.VoiceChannel):
                    await channel.set_permissions(verified_role, view_channel=True, connect=True)
                    await channel.set_permissions(everyone_role, view_channel=False, connect=False)
                else:  # Text channel
                    await channel.set_permissions(verified_role, read_messages=True, send_messages=True)
                    await channel.set_permissions(everyone_role, read_messages=False)
                
                modified_count += 1
                
                # Add a short delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except discord.Forbidden:
                await ctx.send(f"❌ Error: I don't have permission to modify channel {channel.name}.")
            except Exception as e:
                await ctx.send(f"❌ Error setting permissions for {channel.name}: {str(e)}")
        
        # Apply permissions for public channels
        for channel in exception_channels:
            try:
                # Set permissions for everyone role - can see
                if isinstance(channel, discord.VoiceChannel):
                    await channel.set_permissions(everyone_role, view_channel=True, connect=True)
                else:  # Text channel
                    await channel.set_permissions(everyone_role, read_messages=True, read_message_history=True)
                
                modified_count += 1
                
                # Add a short delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except discord.Forbidden:
                await ctx.send(f"❌ Error: I don't have permission to modify channel {channel.name}.")
            except Exception as e:
                await ctx.send(f"❌ Error setting permissions for {channel.name}: {str(e)}")
        
        await status_msg.edit(content=f"✅ Operation complete! Made all channels verified-only except for the specified ones. Modified permissions for {modified_count} channels.")
    
    @channels.command(name="info")
    async def channel_info(self, ctx, channel: discord.TextChannel = None):
        """Display current permission settings for a channel."""
        if channel is None:
            channel = ctx.channel
        
        # Get channel permissions
        embed = discord.Embed(
            title=f"Permissions for #{channel.name}",
            description="Current permission settings for this channel",
            color=discord.Color.blue()
        )
        
        # Get roles with overwrites
        overwrites = channel.overwrites
        
        # Add field for each role with permissions
        for role, overwrite in overwrites.items():
            if isinstance(role, discord.Role):
                perm_list = []
                for perm, value in overwrite:
                    if value is not None:  # Skip neutral permissions
                        perm_status = "✅" if value else "❌"
                        perm_list.append(f"{perm_status} {perm}")
                
                if perm_list:
                    embed.add_field(
                        name=f"Role: {role.name}",
                        value="\n".join(perm_list[:8]) + (f"\n*...and {len(perm_list) - 8} more*" if len(perm_list) > 8 else ""),
                        inline=False
                    )
        
        # Check if channel is in any groups
        in_groups = []
        for group_name, channels in self.permissions_data["channel_groups"].items():
            if channel.id in channels:
                in_groups.append(group_name)
        
        if in_groups:
            embed.add_field(
                name="Channel Groups",
                value=", ".join(in_groups),
                inline=False
            )
        
        # Check if channel is public
        is_public = channel.id in self.permissions_data["public_channels"]
        embed.add_field(
            name="Visibility",
            value="🌍 Public (visible to everyone)" if is_public else "🔒 Restricted (controlled by permissions)",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @channels.group(name="role", invoke_without_command=True)
    async def channel_role(self, ctx):
        """Commands for managing role permissions across channels."""
        embed = discord.Embed(
            title="Role Permission Commands",
            description="Manage permissions for roles across channels",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Available Commands",
            value=(
                f"`{config.PREFIX}channels role view <role>` - View permissions for a role\n"
                f"`{config.PREFIX}channels role allow <role> <permission> <#channel1> [#channel2 ...]` - Allow permission for role\n"
                f"`{config.PREFIX}channels role deny <role> <permission> <#channel1> [#channel2 ...]` - Deny permission for role\n"
                f"`{config.PREFIX}channels role reset <role> <permission> <#channel1> [#channel2 ...]` - Reset permission for role\n"
                f"`{config.PREFIX}channels role copy <from_role> <to_role> [#channel]` - Copy permissions from one role to another\n"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Common Permissions",
            value=(
                "`read_messages` - Can see the channel\n"
                "`send_messages` - Can send messages\n"
                "`embed_links` - Can embed links\n"
                "`attach_files` - Can upload files\n"
                "`read_message_history` - Can read past messages\n"
                "`mention_everyone` - Can mention @everyone\n"
                "`add_reactions` - Can add reactions\n"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    def _resolve_channel(self, guild, channel_input):
        """Resolve a channel from mention, name, or ID."""
        channel = None
        
        # Check if it's a mention (starts with <# and ends with >)
        if channel_input.startswith('<#') and channel_input.endswith('>'):
            try:
                channel_id = int(channel_input[2:-1])
                channel = guild.get_channel(channel_id)
            except (ValueError, TypeError):
                pass
        # Check if it's an ID (all digits)
        elif channel_input.isdigit():
            try:
                channel_id = int(channel_input)
                channel = guild.get_channel(channel_id)
            except (ValueError, TypeError):
                pass
        else:
            # Try to find by name (both text and voice channels)
            channel_name = channel_input.lstrip('#')  # Remove # if present
            channel = discord.utils.get(guild.channels, name=channel_name)
        
        return channel
    
    def _resolve_role(self, guild, role_input):
        """Resolve a role from mention, name, or ID."""
        role = None
        
        # Check if it's a mention (starts with <@ and ends with >)
        if role_input.startswith('<@&') and role_input.endswith('>'):
            try:
                role_id = int(role_input[3:-1])
                role = guild.get_role(role_id)
            except (ValueError, TypeError):
                pass
        # Check if it's an ID (all digits)
        elif role_input.isdigit():
            try:
                role_id = int(role_input)
                role = guild.get_role(role_id)
            except (ValueError, TypeError):
                pass
        else:
            # Try to find by name
            role = discord.utils.get(guild.roles, name=role_input)
        
        return role
    
    def _resolve_user(self, guild, user_input):
        """Resolve a user from mention, name, or ID."""
        user = None
        
        # Check if it's a mention (starts with <@ and ends with >)
        if user_input.startswith('<@') and user_input.endswith('>'):
            # Handle the case where it might be <@!id> format
            user_id_str = user_input.replace('<@!', '').replace('<@', '').replace('>', '')
            try:
                user_id = int(user_id_str)
                user = guild.get_member(user_id)
            except (ValueError, TypeError):
                pass
        # Check if it's an ID (all digits)
        elif user_input.isdigit():
            try:
                user_id = int(user_input)
                user = guild.get_member(user_id)
            except (ValueError, TypeError):
                pass
        else:
            # Try to find by name
            user = discord.utils.find(lambda m: m.name.lower() == user_input.lower() or 
                                   (m.nick and m.nick.lower() == user_input.lower()), guild.members)
        
        return user
    
    @channel_role.command(name="view")
    async def role_view(self, ctx, role_input):
        """View permissions for a specific role across all channels."""
        guild = ctx.guild
        
        # Resolve the role
        role = self._resolve_role(guild, role_input)
        
        if not role:
            return await ctx.send("❌ Role not found. Please specify a valid role mention, name, or ID.")
        
        # Check if this role has any permissions set
        if "role_permissions" not in self.permissions_data or str(role.id) not in self.permissions_data["role_permissions"]:
            return await ctx.send(f"No custom permissions found for role '{role.name}' [ID: {role.id}].")
        
        role_data = self.permissions_data["role_permissions"][str(role.id)]
        
        # Create an embed to display the permissions
        embed = discord.Embed(
            title=f"Permissions for role: {role.name}",
            description=f"Role ID: {role.id}\nColor: {role.color}\nPosition: {role.position}",
            color=role.color
        )
        
        # Add channel-specific permissions
        if "channels" in role_data and role_data["channels"]:
            channel_perms = []
            for channel_id, perms in role_data["channels"].items():
                channel = guild.get_channel(int(channel_id))
                if channel:
                    channel_name = channel.name
                    perm_str = ", ".join([f"{perm} = {value}" for perm, value in perms.items()])
                    channel_perms.append(f"#{channel_name} [ID: {channel_id}]: {perm_str}")
            
            if channel_perms:
                embed.add_field(
                    name="Channel Permissions",
                    value="\n".join(channel_perms) if channel_perms else "None",
                    inline=False
                )
        
        # Add group permissions
        if "groups" in role_data and role_data["groups"]:
            group_perms = []
            for group_name, perms in role_data["groups"].items():
                perm_str = ", ".join([f"{perm} = {value}" for perm, value in perms.items()])
                group_perms.append(f"{group_name}: {perm_str}")
            
            if group_perms:
                embed.add_field(
                    name="Channel Group Permissions",
                    value="\n".join(group_perms) if group_perms else "None",
                    inline=False
                )
        
        await ctx.send(embed=embed)

    @channel_role.command(name="allow")
    async def role_allow(self, ctx, role_input, permission: str, *channel_inputs):
        """Allow a permission for a role in specific channels."""
        if not channel_inputs:
            return await ctx.send("❌ Please specify at least one channel.")
        
        guild = ctx.guild
        
        # Resolve the role
        role = self._resolve_role(guild, role_input)
        
        if not role:
            return await ctx.send("❌ Role not found. Please specify a valid role mention, name, or ID.")
        
        # Validate the permission
        if not hasattr(discord.Permissions, permission):
            return await ctx.send(f"❌ Invalid permission: {permission}")
        
        # Process each channel
        processed_channels = []
        for channel_input in channel_inputs:
            channel = self._resolve_channel(guild, channel_input)
            
            if not channel:
                await ctx.send(f"⚠️ Channel not found: {channel_input}")
                continue
            
            # Update the permissions data
            if "role_permissions" not in self.permissions_data:
                self.permissions_data["role_permissions"] = {}
            
            if str(role.id) not in self.permissions_data["role_permissions"]:
                self.permissions_data["role_permissions"][str(role.id)] = {"channels": {}}
            
            if "channels" not in self.permissions_data["role_permissions"][str(role.id)]:
                self.permissions_data["role_permissions"][str(role.id)]["channels"] = {}
            
            if str(channel.id) not in self.permissions_data["role_permissions"][str(role.id)]["channels"]:
                self.permissions_data["role_permissions"][str(role.id)]["channels"][str(channel.id)] = {}
            
            # Set the permission
            self.permissions_data["role_permissions"][str(role.id)]["channels"][str(channel.id)][permission] = True
            
            # Store the updated channel
            processed_channels.append(f"{channel.name} [ID: {channel.id}]")
            
            try:
                # Apply the permission immediately
                overwrite = channel.overwrites_for(role)
                setattr(overwrite, permission, True)
                await channel.set_permissions(role, overwrite=overwrite)
            except discord.Forbidden:
                await ctx.send(f"❌ Error: I don't have permission to modify channel {channel.name}.")
            except Exception as e:
                await ctx.send(f"❌ Error setting permissions for {channel.name}: {str(e)}")
        
        # Save the updated permissions
        self._save_permissions_data()
        
        if processed_channels:
            channels_text = ", ".join(processed_channels)
            await ctx.send(f"✅ Allowed '{permission}' for role '{role.name}' [ID: {role.id}] in channels: {channels_text}")
        else:
            await ctx.send("❌ No channels were updated.")

    @channel_role.command(name="deny")
    async def role_deny(self, ctx, role_input, permission: str, *channel_inputs):
        """Deny a permission for a role in specific channels."""
        if not channel_inputs:
            return await ctx.send("❌ Please specify at least one channel.")
        
        guild = ctx.guild
        
        # Resolve the role
        role = self._resolve_role(guild, role_input)
        
        if not role:
            return await ctx.send("❌ Role not found. Please specify a valid role mention, name, or ID.")
        
        # Validate the permission
        if not hasattr(discord.Permissions, permission):
            return await ctx.send(f"❌ Invalid permission: {permission}")
        
        # Process each channel
        processed_channels = []
        for channel_input in channel_inputs:
            channel = self._resolve_channel(guild, channel_input)
            
            if not channel:
                await ctx.send(f"⚠️ Channel not found: {channel_input}")
                continue
            
            # Update the permissions data
            if "role_permissions" not in self.permissions_data:
                self.permissions_data["role_permissions"] = {}
            
            if str(role.id) not in self.permissions_data["role_permissions"]:
                self.permissions_data["role_permissions"][str(role.id)] = {"channels": {}}
            
            if "channels" not in self.permissions_data["role_permissions"][str(role.id)]:
                self.permissions_data["role_permissions"][str(role.id)]["channels"] = {}
            
            if str(channel.id) not in self.permissions_data["role_permissions"][str(role.id)]["channels"]:
                self.permissions_data["role_permissions"][str(role.id)]["channels"][str(channel.id)] = {}
            
            # Set the permission
            self.permissions_data["role_permissions"][str(role.id)]["channels"][str(channel.id)][permission] = False
            
            # Store the updated channel
            processed_channels.append(f"{channel.name} [ID: {channel.id}]")
            
            try:
                # Apply the permission immediately
                overwrite = channel.overwrites_for(role)
                setattr(overwrite, permission, False)
                await channel.set_permissions(role, overwrite=overwrite)
            except discord.Forbidden:
                await ctx.send(f"❌ Error: I don't have permission to modify channel {channel.name}.")
            except Exception as e:
                await ctx.send(f"❌ Error setting permissions for {channel.name}: {str(e)}")
        
        # Save the updated permissions
        self._save_permissions_data()
        
        if processed_channels:
            channels_text = ", ".join(processed_channels)
            await ctx.send(f"✅ Denied '{permission}' for role '{role.name}' [ID: {role.id}] in channels: {channels_text}")
        else:
            await ctx.send("❌ No channels were updated.")

    @channel_role.command(name="reset")
    async def role_reset(self, ctx, role_input, permission: str, *channel_inputs):
        """Reset a permission for a role in specific channels."""
        if not channel_inputs:
            return await ctx.send("❌ Please specify at least one channel.")
        
        guild = ctx.guild
        
        # Resolve the role
        role = self._resolve_role(guild, role_input)
        
        if not role:
            return await ctx.send("❌ Role not found. Please specify a valid role mention, name, or ID.")
        
        # Validate the permission
        if not hasattr(discord.Permissions, permission):
            return await ctx.send(f"❌ Invalid permission: {permission}")
        
        # Process each channel
        processed_channels = []
        for channel_input in channel_inputs:
            channel = self._resolve_channel(guild, channel_input)
            
            if not channel:
                await ctx.send(f"⚠️ Channel not found: {channel_input}")
                continue
            
            # Update the permissions data
            if ("role_permissions" in self.permissions_data and 
                str(role.id) in self.permissions_data["role_permissions"] and 
                "channels" in self.permissions_data["role_permissions"][str(role.id)] and 
                str(channel.id) in self.permissions_data["role_permissions"][str(role.id)]["channels"] and 
                permission in self.permissions_data["role_permissions"][str(role.id)]["channels"][str(channel.id)]):
                
                # Remove the permission
                del self.permissions_data["role_permissions"][str(role.id)]["channels"][str(channel.id)][permission]
                
                # Clean up empty dictionaries
                if not self.permissions_data["role_permissions"][str(role.id)]["channels"][str(channel.id)]:
                    del self.permissions_data["role_permissions"][str(role.id)]["channels"][str(channel.id)]
                
                if not self.permissions_data["role_permissions"][str(role.id)]["channels"]:
                    del self.permissions_data["role_permissions"][str(role.id)]["channels"]
                
                if not self.permissions_data["role_permissions"][str(role.id)]:
                    del self.permissions_data["role_permissions"][str(role.id)]
            
            # Store the updated channel
            processed_channels.append(f"{channel.name} [ID: {channel.id}]")
            
            try:
                # Apply the permission reset immediately
                overwrite = channel.overwrites_for(role)
                setattr(overwrite, permission, None)
                
                # Check if all permissions are None, if so, remove the overwrite
                all_none = True
                for perm, value in overwrite:
                    if value is not None:
                        all_none = False
                        break
                
                if all_none:
                    await channel.set_permissions(role, overwrite=None)
                else:
                    await channel.set_permissions(role, overwrite=overwrite)
            except discord.Forbidden:
                await ctx.send(f"❌ Error: I don't have permission to modify channel {channel.name}.")
            except Exception as e:
                await ctx.send(f"❌ Error setting permissions for {channel.name}: {str(e)}")
        
        # Save the updated permissions
        self._save_permissions_data()
        
        if processed_channels:
            channels_text = ", ".join(processed_channels)
            await ctx.send(f"✅ Reset '{permission}' for role '{role.name}' [ID: {role.id}] in channels: {channels_text}")
        else:
            await ctx.send("❌ No channels were updated.")

    @channel_role.command(name="copy")
    async def role_copy_permissions(self, ctx, from_role_input, to_role_input, channel_input=None):
        """Copy permissions from one role to another for all or a specific channel."""
        guild = ctx.guild
        
        # Resolve the source role
        from_role = self._resolve_role(guild, from_role_input)
        
        if not from_role:
            return await ctx.send("❌ Source role not found. Please specify a valid role mention, name, or ID.")
        
        # Resolve the target role
        to_role = self._resolve_role(guild, to_role_input)
        
        if not to_role:
            return await ctx.send("❌ Target role not found. Please specify a valid role mention, name, or ID.")
        
        # Check if we're copying for a specific channel or all channels
        specific_channel = None
        if channel_input:
            specific_channel = self._resolve_channel(guild, channel_input)
            
            if not specific_channel:
                return await ctx.send("❌ Channel not found. Please specify a valid channel mention, name, or ID.")
        
        # Check if the source role has any permissions
        if ("role_permissions" not in self.permissions_data or 
            str(from_role.id) not in self.permissions_data["role_permissions"]):
            return await ctx.send(f"❌ No permissions found for role '{from_role.name}' [ID: {from_role.id}].")
        
        from_role_data = self.permissions_data["role_permissions"][str(from_role.id)]
        
        # Initialize target role data if it doesn't exist
        if "role_permissions" not in self.permissions_data:
            self.permissions_data["role_permissions"] = {}
        
        if str(to_role.id) not in self.permissions_data["role_permissions"]:
            self.permissions_data["role_permissions"][str(to_role.id)] = {}
        
        # Copy channel permissions
        copied_channels = []
        if "channels" in from_role_data and from_role_data["channels"]:
            if "channels" not in self.permissions_data["role_permissions"][str(to_role.id)]:
                self.permissions_data["role_permissions"][str(to_role.id)]["channels"] = {}
            
            for channel_id, perms in from_role_data["channels"].items():
                # Skip if we're only copying for a specific channel
                if specific_channel and str(specific_channel.id) != channel_id:
                    continue
                
                channel = guild.get_channel(int(channel_id))
                if not channel:
                    continue
                
                # Copy the permissions
                self.permissions_data["role_permissions"][str(to_role.id)]["channels"][channel_id] = perms.copy()
                copied_channels.append(channel)
                
                # Apply the permissions immediately
                try:
                    overwrite = discord.PermissionOverwrite()
                    for perm_name, perm_value in perms.items():
                        setattr(overwrite, perm_name, perm_value)
                    
                    await channel.set_permissions(to_role, overwrite=overwrite)
                except discord.Forbidden:
                    await ctx.send(f"❌ Error: I don't have permission to modify channel {channel.name}.")
                except Exception as e:
                    await ctx.send(f"❌ Error setting permissions for {channel.name}: {str(e)}")
        
        # Copy group permissions if we're copying all
        copied_groups = []
        if not specific_channel and "groups" in from_role_data and from_role_data["groups"]:
            if "groups" not in self.permissions_data["role_permissions"][str(to_role.id)]:
                self.permissions_data["role_permissions"][str(to_role.id)]["groups"] = {}
            
            for group_name, perms in from_role_data["groups"].items():
                # Copy the permissions
                self.permissions_data["role_permissions"][str(to_role.id)]["groups"][group_name] = perms.copy()
                copied_groups.append(group_name)
        
        # Save the updated permissions
        self._save_permissions_data()
        
        # Generate response message
        response = f"✅ Copied permissions from role '{from_role.name}' [ID: {from_role.id}] to '{to_role.name}' [ID: {to_role.id}]"
        
        if specific_channel:
            response += f" for channel {specific_channel.name} [ID: {specific_channel.id}]"
        else:
            if copied_channels:
                response += f"\n• Copied channel permissions for {len(copied_channels)} channels"
            
            if copied_groups:
                response += f"\n• Copied group permissions for {len(copied_groups)} groups"
        
        await ctx.send(response)
    
    @channels.command(name="preset")
    async def apply_preset(self, ctx, preset_name: str):
        """Apply a preset permission configuration to your server."""
        preset_name = preset_name.lower()
        
        # Define presets
        presets = {
            "crypto": {
                "public": ["welcome", "rules", "verification", "faq", "announcements"],
                "info_only": ["announcements", "news", "updates"],
                "verified_only": ["general", "chat", "discussion", "price", "trading", "market", "analysis", "signals"],
                "trader_only": ["signals", "vip", "premium"],
                "admin_only": ["admin", "mod", "staff"]
            },
            "community": {
                "public": ["welcome", "rules", "verification", "announcements"],
                "info_only": ["announcements", "news", "updates", "rules"],
                "verified_only": ["general", "chat", "discussion", "media", "memes", "showcase", "support"],
                "admin_only": ["admin", "mod", "staff"]
            },
            "minimal": {
                "public": ["welcome", "rules", "verification"],
                "verified_only": ["general", "chat"],
                "admin_only": ["admin"]
            }
        }
        
        if preset_name not in presets:
            preset_list = ", ".join(presets.keys())
            return await ctx.send(f"❌ Invalid preset. Available presets: {preset_list}")
        
        # Get preset configuration
        preset = presets[preset_name]
        
        # Get role information
        guild = ctx.guild
        verified_role = guild.get_role(config.VERIFIED_ROLE_ID)
        everyone_role = guild.default_role
        
        # Find admin role
        admin_role = None
        for role in guild.roles:
            if "admin" in role.name.lower():
                admin_role = role
                break
        
        # Find trader/premium role
        trader_role = None
        for role in guild.roles:
            if any(keyword in role.name.lower() for keyword in ["trader", "premium", "vip"]):
                trader_role = role
                break
        
        status_msg = await ctx.send(f"Applying '{preset_name}' preset... This may take a moment.")
        
        # Process channels
        public_channels = []
        info_only_channels = []
        verified_only_channels = []
        trader_only_channels = []
        admin_only_channels = []
        
        for channel in guild.text_channels:
            channel_name = channel.name.lower()
            
            # Check channel against each category in the preset
            category_match = False
            
            # Public channels
            for keyword in preset.get("public", []):
                if keyword in channel_name:
                    public_channels.append(channel)
                    category_match = True
                    break
            
            if not category_match:
                # Info-only channels
                for keyword in preset.get("info_only", []):
                    if keyword in channel_name:
                        info_only_channels.append(channel)
                        category_match = True
                        break
            
            if not category_match:
                # Verified-only channels
                for keyword in preset.get("verified_only", []):
                    if keyword in channel_name:
                        verified_only_channels.append(channel)
                        category_match = True
                        break
            
            if not category_match and trader_role:
                # Trader-only channels
                for keyword in preset.get("trader_only", []):
                    if keyword in channel_name:
                        trader_only_channels.append(channel)
                        category_match = True
                        break
            
            if not category_match:
                # Admin-only channels
                for keyword in preset.get("admin_only", []):
                    if keyword in channel_name:
                        admin_only_channels.append(channel)
                        category_match = True
                        break
            
            # If no match was found, default to verified-only
            if not category_match:
                verified_only_channels.append(channel)
        
        try:
            # Update permissions data structure
            self.permissions_data["public_channels"] = [channel.id for channel in public_channels]
            
            # Make sure groups exist
            groups_to_create = ["public", "info_only", "verified_only", "trader_only", "admin_only"]
            for group in groups_to_create:
                if group not in self.permissions_data["channel_groups"]:
                    self.permissions_data["channel_groups"][group] = []
            
            # Update channel groups
            self.permissions_data["channel_groups"]["public"] = [channel.id for channel in public_channels]
            self.permissions_data["channel_groups"]["info_only"] = [channel.id for channel in info_only_channels]
            self.permissions_data["channel_groups"]["verified_only"] = [channel.id for channel in verified_only_channels]
            self.permissions_data["channel_groups"]["trader_only"] = [channel.id for channel in trader_only_channels]
            self.permissions_data["channel_groups"]["admin_only"] = [channel.id for channel in admin_only_channels]
            
            self._save_permissions_data()
            
            # Apply permissions
            modified_count = 0
            
            # First make the public channels public
            for channel in public_channels:
                await channel.set_permissions(verified_role, read_messages=True, send_messages=True)
                await channel.set_permissions(everyone_role, read_messages=True, read_message_history=True)
                modified_count += 1
                await asyncio.sleep(0.3)
            
            # Then make the info-only channels info-only
            for channel in info_only_channels:
                await channel.set_permissions(verified_role, read_messages=True, send_messages=False)
                await channel.set_permissions(everyone_role, read_messages=True, send_messages=False, read_message_history=True)
                modified_count += 1
                await asyncio.sleep(0.3)
            
            # Then make the verified-only channels verified-only
            for channel in verified_only_channels:
                await channel.set_permissions(verified_role, read_messages=True, send_messages=True)
                await channel.set_permissions(everyone_role, read_messages=False)
                modified_count += 1
                await asyncio.sleep(0.3)
            
            # Then make the trader-only channels trader-only
            if trader_role:
                for channel in trader_only_channels:
                    await channel.set_permissions(trader_role, read_messages=True, send_messages=True)
                    await channel.set_permissions(verified_role, read_messages=False)
                    await channel.set_permissions(everyone_role, read_messages=False)
                    modified_count += 1
                    await asyncio.sleep(0.3)
            
            # Then make the admin-only channels admin-only
            if admin_role:
                for channel in admin_only_channels:
                    await channel.set_permissions(admin_role, read_messages=True, send_messages=True)
                    await channel.set_permissions(verified_role, read_messages=False)
                    await channel.set_permissions(everyone_role, read_messages=False)
                    modified_count += 1
                    await asyncio.sleep(0.3)
            
            # Create summary embed
            embed = discord.Embed(
                title=f"✅ '{preset_name.capitalize()}' Preset Applied",
                description="Channel permissions have been configured according to the preset.",
                color=discord.Color.green()
            )
            
            if public_channels:
                embed.add_field(
                    name="🌍 Public Channels",
                    value=", ".join([f"#{ch.name}" for ch in public_channels]),
                    inline=False
                )
            
            if info_only_channels:
                embed.add_field(
                    name="📢 Info-Only Channels",
                    value=", ".join([f"#{ch.name}" for ch in info_only_channels]) + "\n(Everyone can read but not write)",
                    inline=False
                )
            
            if verified_only_channels:
                embed.add_field(
                    name="✅ Verified-Only Channels",
                    value=", ".join([f"#{ch.name}" for ch in verified_only_channels]),
                    inline=False
                )
            
            if trader_only_channels and trader_role:
                embed.add_field(
                    name=f"💎 {trader_role.name}-Only Channels",
                    value=", ".join([f"#{ch.name}" for ch in trader_only_channels]),
                    inline=False
                )
            
            if admin_only_channels and admin_role:
                embed.add_field(
                    name=f"🔒 {admin_role.name}-Only Channels",
                    value=", ".join([f"#{ch.name}" for ch in admin_only_channels]),
                    inline=False
                )
            
            await status_msg.edit(content="Preset applied successfully!")
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ Error: I don't have permission to modify channel permissions.")
        except Exception as e:
            await ctx.send(f"❌ Error applying preset: {str(e)}")
    
    @channels.command(name="apply_permissions")
    async def apply_permissions(self, ctx):
        """Apply all permission settings to channels."""
        guild = ctx.guild
        
        # Get the verified role
        verified_role = guild.get_role(config.VERIFIED_ROLE_ID)
        if not verified_role:
            return await ctx.send("❌ Error: Verified role not found. Please check your configuration.")
        
        # Get everyone role (unverified users)
        everyone_role = guild.default_role
        
        status_msg = await ctx.send("Applying permissions... This may take a moment.")
        
        # Counter for modified channels
        modified_count = 0
        
        # Process all text channels in the server
        for channel in guild.text_channels:
            try:
                # Default permissions
                overwrites = {}
                
                # Set permissions for public channels
                if channel.id in self.permissions_data["public_channels"]:
                    # Public channels - everyone can see
                    overwrites[everyone_role] = discord.PermissionOverwrite(
                        read_messages=True,
                        read_message_history=True
                    )
                else:
                    # Private channels - only verified users can see
                    overwrites[everyone_role] = discord.PermissionOverwrite(
                        read_messages=False
                    )
                
                # Set permissions for verified role
                overwrites[verified_role] = discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True
                )
                
                # Apply role-specific permissions
                for role_id, role_data in self.permissions_data["role_permissions"].items():
                    role = guild.get_role(int(role_id))
                    if not role:
                        continue
                    
                    # Check if this role has channel-specific permissions
                    if "channels" in role_data and str(channel.id) in role_data["channels"]:
                        channel_perms = role_data["channels"][str(channel.id)]
                        
                        # Initialize permission overwrite for this role if needed
                        if role not in overwrites:
                            overwrites[role] = discord.PermissionOverwrite()
                        
                        # Apply each permission
                        for perm_name, perm_value in channel_perms.items():
                            setattr(overwrites[role], perm_name, perm_value)
                    
                    # Check if this channel is in any groups that the role has permissions for
                    if "groups" in role_data:
                        for group_name, group_perms in role_data["groups"].items():
                            if group_name in self.permissions_data["channel_groups"] and \
                               channel.id in self.permissions_data["channel_groups"][group_name]:
                                
                                # Initialize permission overwrite for this role if needed
                                if role not in overwrites:
                                    overwrites[role] = discord.PermissionOverwrite()
                                
                                # Apply each permission
                                for perm_name, perm_value in group_perms.items():
                                    setattr(overwrites[role], perm_name, perm_value)
                
                # Apply the permissions to the channel
                await channel.edit(overwrites=overwrites)
                modified_count += 1
                
                # Add a short delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except discord.Forbidden:
                await ctx.send(f"❌ Error: I don't have permission to modify channel #{channel.name}.")
            except Exception as e:
                await ctx.send(f"❌ Error setting permissions for #{channel.name}: {str(e)}")
        
        await status_msg.edit(content=f"✅ Permission setup complete! Modified permissions for {modified_count} channels.")
    
    @channels.command(name="lockdown")
    async def server_lockdown(self, ctx, mode: str = "all"):
        """
        Quickly lock down the server to prevent spam or raids.
        
        Modes:
        - all: Lock down all channels (default)
        - public: Lock down only public channels
        - verified: Lock down channels for verified users
        - unlock: Remove the lockdown
        """
        guild = ctx.guild
        everyone_role = guild.default_role
        verified_role = guild.get_role(config.VERIFIED_ROLE_ID)
        
        if not verified_role:
            return await ctx.send("❌ Error: Verified role not found. Please check your configuration.")
        
        status_msg = await ctx.send(f"🔒 Starting server lockdown ({mode} mode)... This may take a moment.")
        
        # Counter for modified channels
        modified_count = 0
        
        # Process channels based on mode
        for channel in guild.text_channels:
            try:
                if mode == "unlock":
                    # Remove lockdown - restore previous permissions
                    if channel.id in self.permissions_data.get("locked_channels", []):
                        if "original_permissions" in self.permissions_data and str(channel.id) in self.permissions_data["original_permissions"]:
                            # Get saved original permissions
                            saved_overwrites = {}
                            for role_id, perms in self.permissions_data["original_permissions"][str(channel.id)].items():
                                role = guild.get_role(int(role_id)) if role_id != "everyone" else everyone_role
                                if role:
                                    overwrite = discord.PermissionOverwrite()
                                    for perm_name, perm_value in perms.items():
                                        setattr(overwrite, perm_name, perm_value)
                                    saved_overwrites[role] = overwrite
                            
                            await channel.edit(overwrites=saved_overwrites)
                        else:
                            # No saved permissions, just enable sending for verified
                            await channel.set_permissions(verified_role, send_messages=True)
                            await channel.set_permissions(everyone_role, send_messages=False)
                        
                        modified_count += 1
                
                elif (mode == "all" or 
                     (mode == "public" and channel.id in self.permissions_data.get("public_channels", [])) or
                     (mode == "verified" and channel.id not in self.permissions_data.get("public_channels", []))):
                    
                    # Save current permissions before lockdown if not already saved
                    if "original_permissions" not in self.permissions_data:
                        self.permissions_data["original_permissions"] = {}
                    
                    if str(channel.id) not in self.permissions_data["original_permissions"]:
                        channel_perms = {}
                        for target, overwrite in channel.overwrites.items():
                            target_id = "everyone" if isinstance(target, discord.Role) and target.id == guild.default_role.id else target.id
                            channel_perms[str(target_id)] = {
                                perm: value for perm, value in overwrite.items() if value is not None
                            }
                        self.permissions_data["original_permissions"][str(channel.id)] = channel_perms
                    
                    # Apply lockdown
                    await channel.set_permissions(verified_role, send_messages=False)
                    await channel.set_permissions(everyone_role, send_messages=False)
                    
                    # Track locked channels
                    if "locked_channels" not in self.permissions_data:
                        self.permissions_data["locked_channels"] = []
                    if channel.id not in self.permissions_data["locked_channels"]:
                        self.permissions_data["locked_channels"].append(channel.id)
                    
                    modified_count += 1
                
                # Add a short delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except discord.Forbidden:
                await ctx.send(f"❌ Error: I don't have permission to modify channel {channel.name}.")
            except Exception as e:
                await ctx.send(f"❌ Error setting permissions for {channel.name}: {str(e)}")
        
        # Save the permissions data
        self._save_permissions_data()
        
        if mode == "unlock":
            await status_msg.edit(content=f"🔓 Lockdown removed! Restored permissions for {modified_count} channels.")
        else:
            await status_msg.edit(content=f"🔒 Lockdown complete! Modified permissions for {modified_count} channels. Use `{config.PREFIX}channels lockdown unlock` to remove the lockdown.")
    
    @channels.command(name="restrict_send")
    async def restrict_send(self, ctx, *args):
        """
        Restrict sending messages in channels to specific roles only.
        
        Usage:
        {prefix}channels restrict_send --channels #channel1 #channel2 --roles "Role1" "Role2" "Mod"
        
        This allows only members with the specified roles to send messages in the specified channels,
        while still allowing everyone to read the channels.
        """
        if not args:
            return await ctx.send(f"❌ Usage: `{config.PREFIX}channels restrict_send --channels #channel1 #channel2 --roles \"Role1\" \"Role2\" \"Mod\"`")
            
        # Parse arguments
        channels = []
        roles = []
        current_arg = None
        
        for arg in args:
            if arg in ["--channels", "--roles"]:
                current_arg = arg
                continue
                
            if current_arg == "--channels":
                channel = self._resolve_channel(ctx.guild, arg)
                if channel:
                    channels.append(channel)
                else:
                    await ctx.send(f"⚠️ Could not find channel: {arg}")
            elif current_arg == "--roles":
                role = self._resolve_role(ctx.guild, arg)
                if role:
                    roles.append(role)
                else:
                    await ctx.send(f"⚠️ Could not find role: {arg}")
        
        if not channels:
            return await ctx.send("❌ No valid channels specified.")
            
        if not roles:
            return await ctx.send("❌ No valid roles specified.")
            
        # Create a new channel group for this restriction if it doesn't exist
        restriction_name = f"restricted_send_{int(datetime.datetime.now().timestamp())}"
        if restriction_name not in self.permissions_data["channel_groups"]:
            self.permissions_data["channel_groups"][restriction_name] = []
            
        # Add channels to the restriction group
        for channel in channels:
            if channel.id not in self.permissions_data["channel_groups"][restriction_name]:
                self.permissions_data["channel_groups"][restriction_name].append(channel.id)
        
        self._save_permissions_data()
        
        # Apply permissions
        messages = []
        for channel in channels:
            try:
                # Allow roles to send messages
                for role in roles:
                    # Set specific permissions for allowed roles
                    role_overwrite = discord.PermissionOverwrite()
                    role_overwrite.send_messages = True
                    await channel.set_permissions(role, overwrite=role_overwrite)
                    
                # Deny @everyone send permissions
                everyone_overwrite = discord.PermissionOverwrite()
                everyone_overwrite.send_messages = False
                # We do not change view_channel permission so people can still read
                await channel.set_permissions(ctx.guild.default_role, overwrite=everyone_overwrite)
                
                messages.append(f"✓ {channel.mention}")
            except Exception as e:
                messages.append(f"❌ {channel.mention}: {str(e)}")
        
        # Create summary embed
        embed = discord.Embed(
            title="Channel Send Permission Restriction",
            description=f"Only the following roles can send messages in the specified channels:",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Roles With Send Permissions",
            value="\n".join([f"• {role.name}" for role in roles]) or "None",
            inline=False
        )
        
        embed.add_field(
            name="Channels Modified",
            value="\n".join(messages) or "None",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @channels.command(name="list_restrictions")
    async def list_restrictions(self, ctx):
        """List all channel restrictions currently set up."""
        restriction_groups = []
        
        for group_name, channel_ids in self.permissions_data["channel_groups"].items():
            if group_name.startswith("restricted_send_"):
                # This is a restriction group
                channels = []
                for channel_id in channel_ids:
                    channel = ctx.guild.get_channel(channel_id)
                    if channel:
                        channels.append(channel.mention)
                
                if channels:
                    restriction_groups.append({
                        "name": group_name,
                        "channels": channels
                    })
        
        if not restriction_groups:
            return await ctx.send("No channel restrictions are currently set up.")
        
        # Create embed
        embed = discord.Embed(
            title="Channel Restrictions",
            description="These channels have send permission restrictions:",
            color=discord.Color.blue()
        )
        
        for group in restriction_groups:
            embed.add_field(
                name=f"Restriction Group: {group['name']}",
                value="\n".join(group["channels"]) or "None",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @channels.command(name="setup_xgc_permissions")
    async def setup_xgc_permissions(self, ctx):
        """
        Automatically set up XGC server permissions based on the following structure:
        
        - New User (Before Verification): 
          Can see: Total Members, XRP Price, Verification, Welcome, Rules
          
        - Verified User:
          Can see all general chats, voice channels, raids, giveaways, game nights, and project hub
          Cannot see Alpha Chat or mod channels
          Cannot type in Information Channels
          
        - NFT Holder:
          Same as Verified + can see and chat in Alpha Chat
          
        - XGC (Bots):
          Same as NFT Holder + can access mod channels
          
        - Moderators:
          Can see and type in all channels except bot-only sections
          Can post in Information Channels
          
        - Admins:
          Full access to everything
        """
        guild = ctx.guild
        
        # Get roles or create them if they don't exist
        everyone_role = guild.default_role
        verified_role = discord.utils.get(guild.roles, id=config.VERIFIED_ROLE_ID)
        if not verified_role:
            return await ctx.send("❌ Error: Verified role not found. Please set a VERIFIED_ROLE_ID in config.py")
        
        # Look for other roles
        nft_holder_role = discord.utils.get(guild.roles, name="NFT Holder")
        if not nft_holder_role:
            await ctx.send("⚠️ 'NFT Holder' role not found. Creating it...")
            try:
                nft_holder_role = await guild.create_role(name="NFT Holder", color=discord.Color.purple())
            except Exception as e:
                await ctx.send(f"❌ Error creating NFT Holder role: {str(e)}")
                return
        
        bot_role = discord.utils.get(guild.roles, name="XGC")
        if not bot_role:
            await ctx.send("⚠️ 'XGC' bot role not found. Creating it...")
            try:
                bot_role = await guild.create_role(name="XGC", color=discord.Color.blue())
            except Exception as e:
                await ctx.send(f"❌ Error creating XGC bot role: {str(e)}")
                return
        
        mod_role = discord.utils.get(guild.roles, name="Moderator")
        if not mod_role:
            await ctx.send("⚠️ 'Moderator' role not found. Creating it...")
            try:
                mod_role = await guild.create_role(name="Moderator", color=discord.Color.red())
            except Exception as e:
                await ctx.send(f"❌ Error creating Moderator role: {str(e)}")
                return
        
        admin_role = discord.utils.get(guild.roles, name="Admin")
        if not admin_role:
            await ctx.send("⚠️ 'Admin' role not found. Creating it...")
            try:
                admin_role = await guild.create_role(name="Admin", color=discord.Color.gold())
            except Exception as e:
                await ctx.send(f"❌ Error creating Admin role: {str(e)}")
                return
        
        # Create channel groups
        status_msg = await ctx.send("Setting up channel groups...")
        
        # Define our channel groups
        channel_groups = {
            "public": [],          # Channels visible to unverified users
            "info_only": [],     # Read-only channels for information
            "general": [],         # General channels for verified users
            "alpha": [],           # NFT holder channels
            "mod": [],            # Moderator channels
            "bot": []             # Bot-only channels
        }
        
        # Create the groups in our permissions data
        for group_name in channel_groups.keys():
            if group_name not in self.permissions_data["channel_groups"]:
                self.permissions_data["channel_groups"][group_name] = []
        
        # Auto-categorize channels based on name
        for channel in guild.channels:
            if isinstance(channel, discord.CategoryChannel):
                continue
                
            channel_name = channel.name.lower()
            
            # Public channels detection
            if any(keyword in channel_name for keyword in ["verification", "welcome", "rules", "total-members", "xrp-price", "xrp_price"]):
                if channel.id not in self.permissions_data["channel_groups"]["public"]:
                    self.permissions_data["channel_groups"]["public"].append(channel.id)
                if channel.id not in self.permissions_data["public_channels"]:
                    self.permissions_data["public_channels"].append(channel.id)
                
                # If it's also an information channel
                if any(keyword in channel_name for keyword in ["welcome", "rules", "announcement", "news", "roles"]):
                    if channel.id not in self.permissions_data["channel_groups"]["info_only"]:
                        self.permissions_data["channel_groups"]["info_only"].append(channel.id)
            
            # General channels detection
            elif any(keyword in channel_name for keyword in ["general", "chat", "voice", "raid", "giveaway", "game", "project"]):
                if channel.id not in self.permissions_data["channel_groups"]["general"]:
                    self.permissions_data["channel_groups"]["general"].append(channel.id)
            
            # Alpha channels detection
            elif "alpha" in channel_name:
                if channel.id not in self.permissions_data["channel_groups"]["alpha"]:
                    self.permissions_data["channel_groups"]["alpha"].append(channel.id)
            
            # Mod channels detection
            elif any(keyword in channel_name for keyword in ["mod", "admin", "log", "staff", "bot-log", "modlog", "testing"]):
                if channel.id not in self.permissions_data["channel_groups"]["mod"]:
                    self.permissions_data["channel_groups"]["mod"].append(channel.id)
                
                # If it's specifically a bot channel
                if any(keyword in channel_name for keyword in ["bot-log", "bot_log"]):
                    if channel.id not in self.permissions_data["channel_groups"]["bot"]:
                        self.permissions_data["channel_groups"]["bot"].append(channel.id)
        
        # Save the groups
        self._save_permissions_data()
        
        await status_msg.edit(content="✅ Channel groups set up. Now applying permissions...")
        
        # Set up role permissions
        try:
            # RULE 1: Public channels - visible to everyone
            for channel_id in self.permissions_data["channel_groups"]["public"]:
                channel = guild.get_channel(channel_id)
                if not channel:
                    continue
                
                await channel.set_permissions(everyone_role, view_channel=True, read_messages=True, 
                                            read_message_history=True, send_messages=False)
                await channel.set_permissions(verified_role, view_channel=True, read_messages=True,
                                           read_message_history=True, send_messages=False)
                
                # Special case for verification channel - everyone can send messages there
                if "verification" in channel.name.lower():
                    await channel.set_permissions(everyone_role, send_messages=True)
                
                # Add delay to prevent rate limiting
                await asyncio.sleep(0.5)
            
            # RULE 2: Information channels - no one can send messages except mods and admins
            for channel_id in self.permissions_data["channel_groups"]["info_only"]:
                channel = guild.get_channel(channel_id)
                if not channel:
                    continue
                
                await channel.set_permissions(everyone_role, send_messages=False)
                await channel.set_permissions(verified_role, send_messages=False)
                await channel.set_permissions(nft_holder_role, send_messages=False)
                await channel.set_permissions(mod_role, send_messages=True)
                await channel.set_permissions(admin_role, send_messages=True)
                
                # Add delay to prevent rate limiting
                await asyncio.sleep(0.5)
            
            # RULE 3: General channels - only verified users and above can see
            for channel_id in self.permissions_data["channel_groups"]["general"]:
                channel = guild.get_channel(channel_id)
                if not channel:
                    continue
                
                await channel.set_permissions(everyone_role, view_channel=False, read_messages=False)
                await channel.set_permissions(verified_role, view_channel=True, read_messages=True,
                                           send_messages=True, add_reactions=True)
                
                # Add delay to prevent rate limiting
                await asyncio.sleep(0.5)
            
            # RULE 4: Alpha channels - only NFT holders and above can see
            for channel_id in self.permissions_data["channel_groups"]["alpha"]:
                channel = guild.get_channel(channel_id)
                if not channel:
                    continue
                
                await channel.set_permissions(everyone_role, view_channel=False, read_messages=False)
                await channel.set_permissions(verified_role, view_channel=False, read_messages=False)
                await channel.set_permissions(nft_holder_role, view_channel=True, read_messages=True,
                                          send_messages=True, add_reactions=True)
                
                # Add delay to prevent rate limiting
                await asyncio.sleep(0.5)
            
            # RULE 5: Mod channels - only mods, admins, and bots can see
            for channel_id in self.permissions_data["channel_groups"]["mod"]:
                channel = guild.get_channel(channel_id)
                if not channel:
                    continue
                
                await channel.set_permissions(everyone_role, view_channel=False, read_messages=False)
                await channel.set_permissions(verified_role, view_channel=False, read_messages=False)
                await channel.set_permissions(nft_holder_role, view_channel=False, read_messages=False)
                await channel.set_permissions(bot_role, view_channel=True, read_messages=True, 
                                           send_messages=True)
                await channel.set_permissions(mod_role, view_channel=True, read_messages=True,
                                           send_messages=True)
                await channel.set_permissions(admin_role, view_channel=True, read_messages=True,
                                           send_messages=True)
                
                # Add delay to prevent rate limiting
                await asyncio.sleep(0.5)
            
            # RULE 6: Bot channels - only bots and admins can send messages
            for channel_id in self.permissions_data["channel_groups"]["bot"]:
                channel = guild.get_channel(channel_id)
                if not channel:
                    continue
                
                await channel.set_permissions(mod_role, send_messages=False)
                await channel.set_permissions(bot_role, send_messages=True)
                
                # Add delay to prevent rate limiting
                await asyncio.sleep(0.5)
            
            # Send success message with summary
            embed = discord.Embed(
                title="✅ XGC Server Permissions Setup Complete",
                description="All channel permissions have been set up according to the XGC role hierarchy.",
                color=discord.Color.green()
            )
            
            # Add info about each group to the embed
            public_channels = [guild.get_channel(id).name for id in self.permissions_data["channel_groups"]["public"] if guild.get_channel(id)]
            general_channels = [guild.get_channel(id).name for id in self.permissions_data["channel_groups"]["general"] if guild.get_channel(id)]
            alpha_channels = [guild.get_channel(id).name for id in self.permissions_data["channel_groups"]["alpha"] if guild.get_channel(id)]
            mod_channels = [guild.get_channel(id).name for id in self.permissions_data["channel_groups"]["mod"] if guild.get_channel(id)]
            
            if public_channels:
                embed.add_field(name="Public Channels", value=", ".join(public_channels) if len(public_channels) < 10 else f"{len(public_channels)} channels", inline=False)
            if general_channels:
                embed.add_field(name="General Channels", value=", ".join(general_channels) if len(general_channels) < 10 else f"{len(general_channels)} channels", inline=False)
            if alpha_channels:
                embed.add_field(name="NFT Holder Channels", value=", ".join(alpha_channels) if len(alpha_channels) < 10 else f"{len(alpha_channels)} channels", inline=False)
            if mod_channels:
                embed.add_field(name="Mod Channels", value=", ".join(mod_channels) if len(mod_channels) < 10 else f"{len(mod_channels)} channels", inline=False)
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ Error: I don't have permission to modify channel permissions.")
        except Exception as e:
            await ctx.send(f"❌ Error setting permissions: {str(e)}")
    
    @commands.command(name="quicksetup")
    async def quick_setup(self, ctx):
        """Quickly set up default channel groups and permissions."""
        # Create default groups
        default_groups = ["public", "verified_only", "community", "trading", "announcements", "admin"]
        created_groups = []
        
        for group in default_groups:
            if group not in self.permissions_data["channel_groups"]:
                self.permissions_data["channel_groups"][group] = []
                created_groups.append(group)
        
        # Set up standard permissions
        verified_role = ctx.guild.get_role(config.VERIFIED_ROLE_ID)
        if verified_role:
            role_id = str(verified_role.id)
            
            # Initialize permissions for verified role
            if role_id not in self.permissions_data["role_permissions"]:
                self.permissions_data["role_permissions"][role_id] = {}
            
            if "groups" not in self.permissions_data["role_permissions"][role_id]:
                self.permissions_data["role_permissions"][role_id]["groups"] = {}
            
            # Give verified users access to all verified_only channels
            if "verified_only" not in self.permissions_data["role_permissions"][role_id]["groups"]:
                self.permissions_data["role_permissions"][role_id]["groups"]["verified_only"] = {
                    "read_messages": True,
                    "send_messages": True,
                    "embed_links": True,
                    "attach_files": True,
                    "read_message_history": True
                }
        
        # Save the settings
        self._save_permissions_data()
        
        # Auto-detect channel groups
        welcome_channels = []
        community_channels = []
        trading_channels = []
        admin_channels = []
        
        for channel in ctx.guild.text_channels:
            channel_name = channel.name.lower()
            
            # Auto-categorize by channel name
            if "welcome" in channel_name or "verify" in channel_name or "rules" in channel_name:
                welcome_channels.append(channel)
                if channel.id not in self.permissions_data["public_channels"]:
                    self.permissions_data["public_channels"].append(channel.id)
            
            elif "trading" in channel_name or "market" in channel_name or "price" in channel_name:
                trading_channels.append(channel)
                if "trading" in self.permissions_data["channel_groups"]:
                    if channel.id not in self.permissions_data["channel_groups"]["trading"]:
                        self.permissions_data["channel_groups"]["trading"].append(channel.id)
            
            elif "general" in channel_name or "chat" in channel_name or "discussion" in channel_name:
                community_channels.append(channel)
                if "community" in self.permissions_data["channel_groups"]:
                    if channel.id not in self.permissions_data["channel_groups"]["community"]:
                        self.permissions_data["channel_groups"]["community"].append(channel.id)
            
            elif "admin" in channel_name or "mod" in channel_name or "staff" in channel_name:
                admin_channels.append(channel)
                if "admin" in self.permissions_data["channel_groups"]:
                    if channel.id not in self.permissions_data["channel_groups"]["admin"]:
                        self.permissions_data["channel_groups"]["admin"].append(channel.id)
        
        # Save after auto-categorization
        self._save_permissions_data()
        
        # Send summary
        embed = discord.Embed(
            title="Quick Setup Complete",
            description="Default channel groups and permissions have been set up.",
            color=discord.Color.green()
        )
        
        if created_groups:
            embed.add_field(
                name="Created Groups",
                value=", ".join(created_groups),
                inline=False
            )
        
        if welcome_channels:
            embed.add_field(
                name="Public Channels",
                value=", ".join([f"#{ch.name}" for ch in welcome_channels]),
                inline=False
            )
        
        if community_channels:
            embed.add_field(
                name="Community Channels",
                value=", ".join([f"#{ch.name}" for ch in community_channels]),
                inline=False
            )
        
        if trading_channels:
            embed.add_field(
                name="Trading Channels",
                value=", ".join([f"#{ch.name}" for ch in trading_channels]),
                inline=False
            )
        
        # Apply permissions automatically
        status_msg = await ctx.send("Applying permission settings...")
        
        # Get everyone role
        everyone_role = ctx.guild.default_role
        
        # Apply permissions to channels
        try:
            # Apply permissions to public channels
            for channel in welcome_channels:
                await channel.set_permissions(verified_role, read_messages=True, send_messages=True)
                await channel.set_permissions(everyone_role, read_messages=True, read_message_history=True)
                await asyncio.sleep(0.5)  # Avoid rate limiting
            
            # Apply permissions to other channels - make them verified-only
            all_other_channels = [ch for ch in ctx.guild.text_channels if ch not in welcome_channels]
            for channel in all_other_channels:
                await channel.set_permissions(verified_role, read_messages=True, send_messages=True)
                await channel.set_permissions(everyone_role, read_messages=False)
                await asyncio.sleep(0.5)  # Avoid rate limiting
                
            await status_msg.edit(content="✅ Permission settings applied successfully!")
                
        except discord.Forbidden:
            await ctx.send("❌ Error: I don't have permission to modify channel permissions.")
        except Exception as e:
            await ctx.send(f"❌ Error setting permissions: {str(e)}")
        
        embed.add_field(
            name="Permissions Applied",
            value=(
                f"✅ Public channels are now visible to everyone\n"
                f"✅ All other channels are now visible only to verified users"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdvancedPermissions(bot))
