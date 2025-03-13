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

async def setup(bot):
    await bot.add_cog(RoleManagement(bot))
