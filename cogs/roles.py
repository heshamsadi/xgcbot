import discord
from discord.ext import commands
import config

class RoleManagement(commands.Cog):
    """Commands for role management."""

    def __init__(self, bot):
        self.bot = bot

    # Check if user has moderator permissions
    async def cog_check(self, ctx):
        # Skip check for self-assignable roles command
        if ctx.command.name == "getrole":
            return True
        
        # Check if user has manage roles permission or mod role
        if ctx.author.guild_permissions.manage_roles:
            return True
        
        mod_role = ctx.guild.get_role(config.MOD_ROLE_ID)
        if mod_role and mod_role in ctx.author.roles:
            return True
        
        await ctx.send("You don't have permission to use this command.")
        return False

    # Helper function to resolve role from mention, name, or ID
    def _resolve_role(self, guild, role_input):
        """Resolve a role from mention, name, or ID."""
        role = None
        
        # Check if it's a mention (starts with <@& and ends with >)
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
    
    # Helper function to resolve user from mention, name, or ID
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

    @commands.command(name="role")
    async def assign_role(self, ctx, member: discord.Member, *, role_name: str):
        """Assign a role to a user (Moderator only).
        
        Usage: !role @user RoleName
        """
        # Find the role by name
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        
        if not role:
            return await ctx.send(f"Role '{role_name}' not found.")
        
        # Check if bot has permission to assign this role
        if role.position >= ctx.guild.me.top_role.position:
            return await ctx.send(f"I don't have permission to assign the '{role_name}' role.")
        
        try:
            await member.add_roles(role)
            await ctx.send(f"Added '{role_name}' role to {member.mention}.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to manage roles.")
        except discord.HTTPException:
            await ctx.send("An error occurred while assigning the role.")

    @commands.command(name="getrole")
    async def self_assign_role(self, ctx, *, role_name: str):
        """Self-assign an available role.
        
        Usage: !getrole RoleName
        """
        # Convert role name to lowercase for case-insensitive matching
        role_name_lower = role_name.lower()
        
        # Check if role is self-assignable
        if role_name_lower not in config.SELF_ASSIGNABLE_ROLES:
            available_roles = ', '.join(config.SELF_ASSIGNABLE_ROLES.keys())
            return await ctx.send(
                f"'{role_name}' is not a self-assignable role.\n"
                f"Available roles: {available_roles}"
            )
        
        # Find the role by name (using the original case from config)
        for name, role_id in config.SELF_ASSIGNABLE_ROLES.items():
            if name == role_name_lower:
                # Get role by name
                role = discord.utils.get(ctx.guild.roles, name=role_id)
                break
        
        if not role:
            return await ctx.send(f"Role '{role_name}' not found on the server. Please contact an admin.")
        
        try:
            await ctx.author.add_roles(role)
            await ctx.send(f"You now have the '{role.name}' role!")
        except discord.Forbidden:
            await ctx.send("I don't have permission to assign that role.")
        except discord.HTTPException:
            await ctx.send("An error occurred while assigning the role.")

    @commands.command()
    async def assign(self, ctx, user_input, role_input):
        """Assign a role to a user.
        
        You can use mentions, names, or IDs for both users and roles.
        """
        guild = ctx.guild
        
        # Resolve the user
        member = self._resolve_user(guild, user_input)
        if not member:
            return await ctx.send("❌ User not found. Please specify a valid mention, name, or ID.")
        
        # Resolve the role
        role = self._resolve_role(guild, role_input)
        if not role:
            return await ctx.send("❌ Role not found. Please specify a valid mention, name, or ID.")
        
        try:
            await member.add_roles(role)
            await ctx.send(f"✅ Assigned role '{role.name}' [ID: {role.id}] to {member.name}#{member.discriminator} [ID: {member.id}]")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to assign roles.")
        except Exception as e:
            await ctx.send(f"❌ Error assigning role: {str(e)}")

    @commands.command()
    async def remove(self, ctx, user_input, role_input):
        """Remove a role from a user.
        
        You can use mentions, names, or IDs for both users and roles.
        """
        guild = ctx.guild
        
        # Resolve the user
        member = self._resolve_user(guild, user_input)
        if not member:
            return await ctx.send("❌ User not found. Please specify a valid mention, name, or ID.")
        
        # Resolve the role
        role = self._resolve_role(guild, role_input)
        if not role:
            return await ctx.send("❌ Role not found. Please specify a valid mention, name, or ID.")
        
        try:
            await member.remove_roles(role)
            await ctx.send(f"✅ Removed role '{role.name}' [ID: {role.id}] from {member.name}#{member.discriminator} [ID: {member.id}]")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to remove roles.")
        except Exception as e:
            await ctx.send(f"❌ Error removing role: {str(e)}")

    @commands.command()
    async def role_info(self, ctx, role_input):
        """Get information about a role.
        
        You can use a role mention, name, or ID.
        """
        guild = ctx.guild
        
        # Resolve the role
        role = self._resolve_role(guild, role_input)
        if not role:
            return await ctx.send("❌ Role not found. Please specify a valid mention, name, or ID.")

async def setup(bot):
    await bot.add_cog(RoleManagement(bot))
