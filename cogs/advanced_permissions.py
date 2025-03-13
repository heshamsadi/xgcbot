import discord
from discord.ext import commands
import config
import asyncio
import json
import os
from typing import Optional, List, Dict, Union, Tuple

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
    async def set_channel_permission(self, ctx, channel: discord.TextChannel, role_name: str, permission: str, value: bool):
        """Set a permission for a role in a specific channel."""
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
        
        # Initialize channel permissions for this role if needed
        if "channels" not in self.permissions_data["role_permissions"][str(role.id)]:
            self.permissions_data["role_permissions"][str(role.id)]["channels"] = {}
        
        # Set the permission
        if str(channel.id) not in self.permissions_data["role_permissions"][str(role.id)]["channels"]:
            self.permissions_data["role_permissions"][str(role.id)]["channels"][str(channel.id)] = {}
        
        self.permissions_data["role_permissions"][str(role.id)]["channels"][str(channel.id)][permission] = value
        self._save_permissions_data()
        
        permission_status = "allowed" if value else "denied"
        await ctx.send(f"✅ Set permission '{permission}' to {permission_status} for role '{role_name}' in channel #{channel.name}")
    
    @channels.command(name="set_public")
    async def set_public_channels(self, ctx, *channels: discord.TextChannel):
        """Make channels visible to everyone."""
        if not channels:
            return await ctx.send("❌ Please specify at least one channel to make public.")
        
        # Add channels to public list
        added_channels = []
        for channel in channels:
            if channel.id not in self.permissions_data["public_channels"]:
                self.permissions_data["public_channels"].append(channel.id)
                added_channels.append(f"#{channel.name}")
        
        self._save_permissions_data()
        
        # Immediately apply permissions to these channels
        guild = ctx.guild
        
        # Get the verified role
        verified_role = guild.get_role(config.VERIFIED_ROLE_ID)
        if not verified_role:
            await ctx.send("❌ Error: Verified role not found. Please check your configuration.")
            if added_channels:
                added_text = ", ".join(added_channels)
                return await ctx.send(f"✅ Added {added_text} to public channels, but could not apply permissions.")
            return
        
        # Get everyone role (unverified users)
        everyone_role = guild.default_role
        
        status_msg = await ctx.send("Setting permissions for these channels...")
        
        try:
            for channel in channels:
                # Set permissions
                await channel.set_permissions(verified_role, read_messages=True, send_messages=True)
                await channel.set_permissions(everyone_role, read_messages=True, read_message_history=True)
        
            await status_msg.edit(content=f"✅ Made {', '.join([f'#{c.name}' for c in channels])} public (visible to everyone) and applied permissions.")
            
        except discord.Forbidden:
            await ctx.send("❌ Error: I don't have permission to modify channel permissions.")
        except Exception as e:
            await ctx.send(f"❌ Error setting permissions: {str(e)}")
    
    @channels.command(name="set_verified_only")
    async def set_verified_only_channels(self, ctx, *channels: discord.TextChannel):
        """Make channels visible only to verified users."""
        if not channels:
            return await ctx.send("❌ Please specify at least one channel to make verified-only.")
        
        # Remove channels from public list
        removed_channels = []
        for channel in channels:
            if channel.id in self.permissions_data["public_channels"]:
                self.permissions_data["public_channels"].remove(channel.id)
                removed_channels.append(f"#{channel.name}")
        
        # Add channels to verified_only group if it exists
        if "verified_only" in self.permissions_data["channel_groups"]:
            for channel in channels:
                if channel.id not in self.permissions_data["channel_groups"]["verified_only"]:
                    self.permissions_data["channel_groups"]["verified_only"].append(channel.id)
        
        self._save_permissions_data()
        
        # Immediately apply permissions to these channels
        guild = ctx.guild
        
        # Get the verified role
        verified_role = guild.get_role(config.VERIFIED_ROLE_ID)
        if not verified_role:
            await ctx.send("❌ Error: Verified role not found. Please check your configuration.")
            if removed_channels:
                removed_text = ", ".join(removed_channels)
                return await ctx.send(f"✅ Added {removed_text} to verified-only channels, but could not apply permissions.")
            return
        
        # Get everyone role (unverified users)
        everyone_role = guild.default_role
        
        status_msg = await ctx.send("Setting permissions for these channels...")
        
        try:
            for channel in channels:
                # Set permissions
                await channel.set_permissions(verified_role, read_messages=True, send_messages=True)
                await channel.set_permissions(everyone_role, read_messages=False)
        
            await status_msg.edit(content=f"✅ Made {', '.join([f'#{c.name}' for c in channels])} verified-only (only visible to verified users) and applied permissions.")
            
        except discord.Forbidden:
            await ctx.send("❌ Error: I don't have permission to modify channel permissions.")
        except Exception as e:
            await ctx.send(f"❌ Error setting permissions: {str(e)}")
    
    @channels.command(name="all_verified_only")
    async def set_all_verified_only(self, ctx, *channel_args):
        """
        Make ALL channels verified-only EXCEPT the specified channels.
        Usage: !channels all_verified_only #welcome #rules #verification
            OR: !channels all_verified_only welcome rules verification
        This will make all channels except those listed visible only to verified users.
        """
        guild = ctx.guild
        
        # Convert text names to channel objects
        exclude_channels = []
        for arg in channel_args:
            # Check if it's a channel mention
            if arg.startswith("<#") and arg.endswith(">"):
                channel_id = int(arg[2:-1])
                channel = guild.get_channel(channel_id)
                if channel:
                    exclude_channels.append(channel)
            # Otherwise treat as channel name
            else:
                # Remove any spaces or special characters from input
                clean_name = arg.lower().strip()
                for channel in guild.text_channels:
                    # Clean the channel name for comparison
                    clean_channel_name = channel.name.lower().replace('-', '').replace('_', '').replace('・', '')
                    arg_clean = clean_name.replace('-', '').replace('_', '').replace('・', '')
                    
                    # Check if the name is in the channel name
                    if arg_clean in clean_channel_name:
                        exclude_channels.append(channel)
                        break
        
        if not exclude_channels:
            return await ctx.send("❌ Could not find any matching channels. Please use #channel mentions or valid channel names.")
        
        # Get all text channels
        all_channels = guild.text_channels
        
        # Filter out excluded channels
        excluded_ids = [channel.id for channel in exclude_channels]
        channels_to_restrict = [channel for channel in all_channels if channel.id not in excluded_ids]
        
        if not channels_to_restrict:
            return await ctx.send("❌ No channels to restrict. Make sure you're not excluding all channels.")
        
        # Get the verified role
        verified_role = guild.get_role(config.VERIFIED_ROLE_ID)
        if not verified_role:
            return await ctx.send("❌ Error: Verified role not found. Please check your configuration.")
        
        # Get everyone role (unverified users)
        everyone_role = guild.default_role
        
        status_msg = await ctx.send(f"Making {len(channels_to_restrict)} channels verified-only... This may take a moment.")
        
        try:
            # Update permissions data
            self.permissions_data["public_channels"] = excluded_ids
            
            # Make sure verified_only group exists
            if "verified_only" not in self.permissions_data["channel_groups"]:
                self.permissions_data["channel_groups"]["verified_only"] = []
            
            # Add all channels to verified_only group
            for channel in channels_to_restrict:
                if channel.id not in self.permissions_data["channel_groups"]["verified_only"]:
                    self.permissions_data["channel_groups"]["verified_only"].append(channel.id)
            
            self._save_permissions_data()
            
            # Apply permissions
            modified_count = 0
            excluded_count = 0
            
            # First make the excluded channels public
            for channel in exclude_channels:
                await channel.set_permissions(verified_role, read_messages=True, send_messages=True)
                await channel.set_permissions(everyone_role, read_messages=True, read_message_history=True)
                excluded_count += 1
                await asyncio.sleep(0.5)  # Avoid rate limiting
            
            # Then make all other channels verified-only
            for channel in channels_to_restrict:
                await channel.set_permissions(verified_role, read_messages=True, send_messages=True)
                await channel.set_permissions(everyone_role, read_messages=False)
                modified_count += 1
                await asyncio.sleep(0.5)  # Avoid rate limiting
            
            await status_msg.edit(content=f"✅ Permission setup complete!\n"
                                        f"• {excluded_count} public channels (visible to everyone): {', '.join([f'#{c.name}' for c in exclude_channels])}\n"
                                        f"• {modified_count} verified-only channels (hidden from unverified users)")
            
        except discord.Forbidden:
            await ctx.send("❌ Error: I don't have permission to modify channel permissions.")
        except Exception as e:
            await ctx.send(f"❌ Error setting permissions: {str(e)}")
    
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
    
    @channel_role.command(name="view")
    async def view_role_perms(self, ctx, *, role_name: str):
        """View permissions for a role across all channels."""
        # Find the role
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send(f"❌ Role '{role_name}' not found.")
        
        embed = discord.Embed(
            title=f"Permissions for {role.name}",
            description="Permissions across different channels",
            color=role.color
        )
        
        # Check permissions in each channel
        channels_with_perms = []
        for channel in ctx.guild.text_channels:
            overwrite = channel.overwrites_for(role)
            if overwrite._values:  # Has some permissions set
                perm_list = []
                for perm, value in overwrite:
                    if value is not None:  # Skip neutral permissions
                        perm_status = "✅" if value else "❌"
                        perm_list.append(f"{perm_status} {perm}")
                
                if perm_list:
                    channels_with_perms.append((channel, perm_list))
        
        # Sort channels by permission count
        channels_with_perms.sort(key=lambda x: len(x[1]), reverse=True)
        
        # Add fields for channels with permissions
        for channel, perm_list in channels_with_perms[:10]:  # Limit to avoid too many fields
            embed.add_field(
                name=f"#{channel.name}",
                value="\n".join(perm_list[:5]) + (f"\n*...and {len(perm_list) - 5} more*" if len(perm_list) > 5 else ""),
                inline=True
            )
        
        if len(channels_with_perms) > 10:
            embed.add_field(
                name="More Channels",
                value=f"*...and {len(channels_with_perms) - 10} more channels*",
                inline=False
            )
        elif not channels_with_perms:
            embed.add_field(
                name="No Custom Permissions",
                value=f"This role has no custom permissions set in any channels.",
                inline=False
            )
        
        # Check if role is in any group permissions
        role_id = str(role.id)
        if role_id in self.permissions_data["role_permissions"]:
            if "groups" in self.permissions_data["role_permissions"][role_id]:
                group_perms = self.permissions_data["role_permissions"][role_id]["groups"]
                if group_perms:
                    embed.add_field(
                        name="Group Permissions",
                        value="\n".join([f"**{group}**: " + ", ".join([f"{p} ({v})" for p, v in perms.items()][:3]) for group, perms in group_perms.items()]),
                        inline=False
                    )
        
        await ctx.send(embed=embed)
    
    @channel_role.command(name="allow")
    async def role_allow_perm(self, ctx, role_name: str, permission: str, *channels: discord.TextChannel):
        """Allow a permission for a role in specified channels."""
        # Find the role
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send(f"❌ Role '{role_name}' not found.")
        
        # Validate the permission
        try:
            getattr(discord.Permissions(), permission)
        except AttributeError:
            return await ctx.send(f"❌ '{permission}' is not a valid permission. Use `!channels role` to see valid permissions.")
        
        if not channels:
            return await ctx.send("❌ Please specify at least one channel.")
        
        status_msg = await ctx.send(f"Setting permissions... This may take a moment.")
        
        try:
            success_channels = []
            for channel in channels:
                overwrite = channel.overwrites_for(role)
                setattr(overwrite, permission, True)
                await channel.set_permissions(role, overwrite=overwrite)
                success_channels.append(channel.name)
                await asyncio.sleep(0.5)  # Avoid rate limiting
            
            await status_msg.edit(content=f"✅ Allowed '{permission}' for role '{role.name}' in channels: {', '.join(['#' + name for name in success_channels])}")
            
        except discord.Forbidden:
            await ctx.send("❌ Error: I don't have permission to modify channel permissions.")
        except Exception as e:
            await ctx.send(f"❌ Error setting permissions: {str(e)}")
    
    @channel_role.command(name="deny")
    async def role_deny_perm(self, ctx, role_name: str, permission: str, *channels: discord.TextChannel):
        """Deny a permission for a role in specified channels."""
        # Find the role
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send(f"❌ Role '{role_name}' not found.")
        
        # Validate the permission
        try:
            getattr(discord.Permissions(), permission)
        except AttributeError:
            return await ctx.send(f"❌ '{permission}' is not a valid permission. Use `!channels role` to see valid permissions.")
        
        if not channels:
            return await ctx.send("❌ Please specify at least one channel.")
        
        status_msg = await ctx.send(f"Setting permissions... This may take a moment.")
        
        try:
            success_channels = []
            for channel in channels:
                overwrite = channel.overwrites_for(role)
                setattr(overwrite, permission, False)
                await channel.set_permissions(role, overwrite=overwrite)
                success_channels.append(channel.name)
                await asyncio.sleep(0.5)  # Avoid rate limiting
            
            await status_msg.edit(content=f"✅ Denied '{permission}' for role '{role.name}' in channels: {', '.join(['#' + name for name in success_channels])}")
            
        except discord.Forbidden:
            await ctx.send("❌ Error: I don't have permission to modify channel permissions.")
        except Exception as e:
            await ctx.send(f"❌ Error setting permissions: {str(e)}")
    
    @channel_role.command(name="reset")
    async def role_reset_perm(self, ctx, role_name: str, permission: str, *channels: discord.TextChannel):
        """Reset a permission for a role in specified channels."""
        # Find the role
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send(f"❌ Role '{role_name}' not found.")
        
        # Validate the permission
        try:
            getattr(discord.Permissions(), permission)
        except AttributeError:
            return await ctx.send(f"❌ '{permission}' is not a valid permission. Use `!channels role` to see valid permissions.")
        
        if not channels:
            return await ctx.send("❌ Please specify at least one channel.")
        
        status_msg = await ctx.send(f"Resetting permissions... This may take a moment.")
        
        try:
            success_channels = []
            for channel in channels:
                overwrite = channel.overwrites_for(role)
                setattr(overwrite, permission, None)
                
                # Check if all permissions are now None (neutral)
                is_empty = True
                for perm, value in overwrite:
                    if value is not None:
                        is_empty = False
                        break
                
                if is_empty:
                    # Remove the entire overwrite if all permissions are neutral
                    await channel.set_permissions(role, overwrite=None)
                else:
                    await channel.set_permissions(role, overwrite=overwrite)
                    
                success_channels.append(channel.name)
                await asyncio.sleep(0.5)  # Avoid rate limiting
            
            await status_msg.edit(content=f"✅ Reset '{permission}' for role '{role.name}' in channels: {', '.join(['#' + name for name in success_channels])}")
            
        except discord.Forbidden:
            await ctx.send("❌ Error: I don't have permission to modify channel permissions.")
        except Exception as e:
            await ctx.send(f"❌ Error setting permissions: {str(e)}")
    
    @channel_role.command(name="copy")
    async def role_copy_perms(self, ctx, from_role: str, to_role: str, channel: discord.TextChannel = None):
        """Copy permissions from one role to another."""
        # Find the roles
        role_from = discord.utils.get(ctx.guild.roles, name=from_role)
        if not role_from:
            return await ctx.send(f"❌ Source role '{from_role}' not found.")
            
        role_to = discord.utils.get(ctx.guild.roles, name=to_role)
        if not role_to:
            return await ctx.send(f"❌ Target role '{to_role}' not found.")
        
        # If no channel is specified, copy for all channels
        channels_to_update = [channel] if channel else ctx.guild.text_channels
        
        status_msg = await ctx.send(f"Copying permissions from '{role_from.name}' to '{role_to.name}'... This may take a moment.")
        
        try:
            updated_count = 0
            
            for ch in channels_to_update:
                # Get overwrite for source role
                from_overwrite = ch.overwrites_for(role_from)
                
                # Apply to target role if overwrite exists
                if from_overwrite._values:
                    await ch.set_permissions(role_to, overwrite=from_overwrite)
                    updated_count += 1
                
                await asyncio.sleep(0.5)  # Avoid rate limiting
            
            if channel:
                await status_msg.edit(content=f"✅ Copied permissions from '{role_from.name}' to '{role_to.name}' in #{channel.name}")
            else:
                await status_msg.edit(content=f"✅ Copied permissions from '{role_from.name}' to '{role_to.name}' in {updated_count} channels")
            
        except discord.Forbidden:
            await ctx.send("❌ Error: I don't have permission to modify channel permissions.")
        except Exception as e:
            await ctx.send(f"❌ Error copying permissions: {str(e)}")
    
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
            
            # Apply permissions to public channels
            for channel in public_channels:
                await channel.set_permissions(verified_role, read_messages=True, send_messages=True)
                await channel.set_permissions(everyone_role, read_messages=True, read_message_history=True)
                await asyncio.sleep(0.3)
            
            # Apply permissions to info-only channels
            for channel in info_only_channels:
                await channel.set_permissions(verified_role, read_messages=True, send_messages=False)
                await channel.set_permissions(everyone_role, read_messages=True, send_messages=False, read_message_history=True)
                await asyncio.sleep(0.3)
            
            # Apply permissions to verified-only channels
            for channel in verified_only_channels:
                await channel.set_permissions(verified_role, read_messages=True, send_messages=True)
                await channel.set_permissions(everyone_role, read_messages=False)
                await asyncio.sleep(0.3)
            
            # Apply permissions to trader-only channels
            if trader_role:
                for channel in trader_only_channels:
                    await channel.set_permissions(trader_role, read_messages=True, send_messages=True)
                    await channel.set_permissions(verified_role, read_messages=False)
                    await channel.set_permissions(everyone_role, read_messages=False)
                    await asyncio.sleep(0.3)
            
            # Apply permissions to admin-only channels
            if admin_role:
                for channel in admin_only_channels:
                    await channel.set_permissions(admin_role, read_messages=True, send_messages=True)
                    await channel.set_permissions(verified_role, read_messages=False)
                    await channel.set_permissions(everyone_role, read_messages=False)
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
                await ctx.send(f"❌ Error: I don't have permission to modify channel #{channel.name}.")
            except Exception as e:
                await ctx.send(f"❌ Error setting permissions for #{channel.name}: {str(e)}")
        
        # Save the permissions data
        self._save_permissions_data()
        
        if mode == "unlock":
            await status_msg.edit(content=f"🔓 Lockdown removed! Restored permissions for {modified_count} channels.")
        else:
            await status_msg.edit(content=f"🔒 Lockdown complete! Modified permissions for {modified_count} channels. Use `{config.PREFIX}channels lockdown unlock` to remove the lockdown.")
    
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
