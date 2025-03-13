import discord
from discord.ext import commands
import config
import asyncio

class Moderation(commands.Cog):
    """Commands for server moderation."""

    def __init__(self, bot):
        self.bot = bot

    # Check if user has moderator permissions
    async def cog_check(self, ctx):
        # Check if user has manage messages permission or mod role
        if ctx.author.guild_permissions.ban_members:
            return True
        
        mod_role = ctx.guild.get_role(config.MOD_ROLE_ID)
        if mod_role and mod_role in ctx.author.roles:
            return True
        
        await ctx.send("You don't have permission to use this command.")
        return False

    @commands.command(name="kick")
    async def kick_member(self, ctx, member: discord.Member, *, reason=None):
        """Kick a member from the server.
        
        Usage: !kick @user [reason]
        """
        # Check if the bot can kick the user
        if member.top_role >= ctx.guild.me.top_role:
            return await ctx.send("I cannot kick this user due to role hierarchy.")
        
        # Check if the command user is trying to kick someone with same/higher role
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("You cannot kick someone with the same or higher role than you.")
        
        # Format reason
        if reason:
            full_reason = f"Kicked by {ctx.author}: {reason}"
        else:
            full_reason = f"Kicked by {ctx.author}"
        
        try:
            # Attempt to send a DM to the user
            try:
                await member.send(f"You have been kicked from {ctx.guild.name}.\nReason: {full_reason}")
            except discord.Forbidden:
                # User has DMs disabled
                pass
            
            # Kick the user
            await member.kick(reason=full_reason)
            
            # Send confirmation message
            embed = discord.Embed(
                title="Member Kicked",
                description=f"{member.mention} has been kicked from the server.",
                color=discord.Color.orange()
            )
            embed.add_field(name="Reason", value=reason or "No reason provided")
            embed.set_footer(text=f"Kicked by {ctx.author}")
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to kick members.")
        except discord.HTTPException:
            await ctx.send("An error occurred while trying to kick the member.")

    @commands.command(name="ban")
    async def ban_member(self, ctx, member: discord.Member, *, reason=None):
        """Ban a member from the server.
        
        Usage: !ban @user [reason]
        """
        # Check if the bot can ban the user
        if member.top_role >= ctx.guild.me.top_role:
            return await ctx.send("I cannot ban this user due to role hierarchy.")
        
        # Check if the command user is trying to ban someone with same/higher role
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("You cannot ban someone with the same or higher role than you.")
        
        # Format reason
        if reason:
            full_reason = f"Banned by {ctx.author}: {reason}"
        else:
            full_reason = f"Banned by {ctx.author}"
        
        try:
            # Attempt to send a DM to the user
            try:
                await member.send(f"You have been banned from {ctx.guild.name}.\nReason: {full_reason}")
            except discord.Forbidden:
                # User has DMs disabled
                pass
            
            # Ban the user
            await member.ban(reason=full_reason, delete_message_days=0)
            
            # Send confirmation message
            embed = discord.Embed(
                title="Member Banned",
                description=f"{member.mention} has been banned from the server.",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason or "No reason provided")
            embed.set_footer(text=f"Banned by {ctx.author}")
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban members.")
        except discord.HTTPException:
            await ctx.send("An error occurred while trying to ban the member.")

    @commands.command(name="clear")
    async def clear_messages(self, ctx, amount: int = 10):
        """Clear a specified number of messages from the channel.
        
        Usage: !clear [amount]
        Default amount: 10
        Maximum amount: 100
        """
        # Check if amount is valid
        if amount <= 0:
            return await ctx.send("The number of messages to clear must be positive.")
        
        if amount > 100:
            return await ctx.send("You can only clear up to 100 messages at once.")
        
        # Delete the command message first
        await ctx.message.delete()
        
        # Purge the messages
        deleted = await ctx.channel.purge(limit=amount)
        
        # Send confirmation message
        confirmation = await ctx.send(f"Deleted {len(deleted)} messages.")
        
        # Delete the confirmation message after 3 seconds
        await asyncio.sleep(3)
        await confirmation.delete()

async def setup(bot):
    await bot.add_cog(Moderation(bot))
