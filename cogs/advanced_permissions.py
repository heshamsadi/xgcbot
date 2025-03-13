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
    
    def save_permissions(self):
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
        self.save_permissions()
        
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
        
        self.save_permissions()
        
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
        
        self.save_permissions()
        
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
        self.save_permissions()
        
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
        self.save_permissions()
        
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
        
        self.save_permissions()
        
        if added_channels:
            added_text = ", ".join(added_channels)
            await ctx.send(f"✅ Made {added_text} public (visible to everyone)")
        else:
            await ctx.send(f"ℹ️ All specified channels were already public")
    
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
        
        self.save_permissions()
        
        if removed_channels:
            removed_text = ", ".join(removed_channels)
            await ctx.send(f"✅ Made {removed_text} verified-only (only visible to verified users)")
        else:
            await ctx.send(f"ℹ️ All specified channels were already verified-only")
    
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
                await asyncio.sleep(1)
                
            except discord.Forbidden:
                await ctx.send(f"❌ Error: I don't have permission to modify channel #{channel.name}.")
            except Exception as e:
                await ctx.send(f"❌ Error setting permissions for #{channel.name}: {str(e)}")
        
        await status_msg.edit(content=f"✅ Permission setup complete! Modified permissions for {modified_count} channels.")
    
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
        self.save_permissions()
        
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
        self.save_permissions()
        
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
        
        embed.add_field(
            name="Next Steps",
            value=(
                f"1. Review channel groups with `{config.PREFIX}channels list`\n"
                f"2. Apply permissions with `{config.PREFIX}channels apply_permissions`\n"
                f"3. Make adjustments as needed with `{config.PREFIX}channels` commands"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdvancedPermissions(bot))
