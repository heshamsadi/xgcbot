import discord
from discord.ext import commands
import config
import asyncio
import datetime

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

    @commands.command(name="kick")
    async def kick_member(self, ctx, user_input, *, reason=None):
        """Kick a user from the server.
        
        You can use a username, mention, or user ID.
        """
        # Get the target member
        guild = ctx.guild
        member = self._resolve_user(guild, user_input)
        
        if not member:
            return await ctx.send(f"❌ User not found. Please specify a valid mention, name, or ID.")
        
        # Confirm before kicking
        confirm_msg = f"Are you sure you want to kick {member.name}#{member.discriminator} [ID: {member.id}]?"
        if reason:
            confirm_msg += f"\nReason: {reason}"
        confirm_msg += "\nRespond with 'yes' to confirm or 'no' to cancel."
        
        await ctx.send(confirm_msg)
        
        # Wait for confirmation
        try:
            response = await self.bot.wait_for(
                'message',
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no'],
                timeout=30.0
            )
            
            if response.content.lower() == 'no':
                return await ctx.send("✅ Kick cancelled.")
            
        except asyncio.TimeoutError:
            return await ctx.send("⏱️ Kick cancelled due to timeout.")
        
        # Perform the kick
        try:
            await member.kick(reason=reason)
            await ctx.send(f"✅ {member.name}#{member.discriminator} [ID: {member.id}] has been kicked.")
            
            # Log the action
            log_channel = discord.utils.get(ctx.guild.text_channels, name='mod-logs')
            if log_channel:
                embed = discord.Embed(
                    title="Member Kicked",
                    description=f"{member.mention} was kicked by {ctx.author.mention}",
                    color=discord.Color.red()
                )
                embed.add_field(name="Reason", value=reason or "No reason provided")
                embed.add_field(name="User ID", value=member.id)
                embed.add_field(name="Timestamp", value=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                await log_channel.send(embed=embed)
                
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to kick this member.")
        except Exception as e:
            await ctx.send(f"❌ Error kicking member: {str(e)}")

    @commands.command(name="ban")
    async def ban_member(self, ctx, user_input, *, reason=None):
        """Ban a user from the server.
        
        You can use a username, mention, or user ID.
        """
        # Get the target member
        guild = ctx.guild
        member = self._resolve_user(guild, user_input)
        
        if not member:
            # Try to ban by ID if member is not in the server
            if user_input.isdigit():
                user_id = int(user_input)
                confirm_msg = f"Are you sure you want to ban user with ID: {user_id}? This user is not in the server."
                if reason:
                    confirm_msg += f"\nReason: {reason}"
                confirm_msg += "\nRespond with 'yes' to confirm or 'no' to cancel."
                
                await ctx.send(confirm_msg)
                
                # Wait for confirmation
                try:
                    response = await self.bot.wait_for(
                        'message',
                        check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no'],
                        timeout=30.0
                    )
                    
                    if response.content.lower() == 'no':
                        return await ctx.send("✅ Ban cancelled.")
                    
                except asyncio.TimeoutError:
                    return await ctx.send("⏱️ Ban cancelled due to timeout.")
                
                # Perform the ban by ID
                try:
                    await ctx.guild.ban(discord.Object(id=user_id), reason=reason, delete_message_days=1)
                    await ctx.send(f"✅ User with ID: {user_id} has been banned.")
                    
                    # Log the action
                    log_channel = discord.utils.get(ctx.guild.text_channels, name='mod-logs')
                    if log_channel:
                        embed = discord.Embed(
                            title="User Banned",
                            description=f"User with ID: {user_id} was banned by {ctx.author.mention}",
                            color=discord.Color.dark_red()
                        )
                        embed.add_field(name="Reason", value=reason or "No reason provided")
                        embed.add_field(name="Timestamp", value=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        await log_channel.send(embed=embed)
                    
                    return
                except Exception as e:
                    return await ctx.send(f"❌ Error banning user: {str(e)}")
            else:
                return await ctx.send(f"❌ User not found. Please specify a valid mention, name, or ID.")
        
        # Confirm before banning
        confirm_msg = f"Are you sure you want to ban {member.name}#{member.discriminator} [ID: {member.id}]?"
        if reason:
            confirm_msg += f"\nReason: {reason}"
        confirm_msg += "\nRespond with 'yes' to confirm or 'no' to cancel."
        
        await ctx.send(confirm_msg)
        
        # Wait for confirmation
        try:
            response = await self.bot.wait_for(
                'message',
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no'],
                timeout=30.0
            )
            
            if response.content.lower() == 'no':
                return await ctx.send("✅ Ban cancelled.")
            
        except asyncio.TimeoutError:
            return await ctx.send("⏱️ Ban cancelled due to timeout.")
        
        # Perform the ban
        try:
            await member.ban(reason=reason, delete_message_days=1)
            await ctx.send(f"✅ {member.name}#{member.discriminator} [ID: {member.id}] has been banned.")
            
            # Log the action
            log_channel = discord.utils.get(ctx.guild.text_channels, name='mod-logs')
            if log_channel:
                embed = discord.Embed(
                    title="Member Banned",
                    description=f"{member.mention} was banned by {ctx.author.mention}",
                    color=discord.Color.dark_red()
                )
                embed.add_field(name="Reason", value=reason or "No reason provided")
                embed.add_field(name="User ID", value=member.id)
                embed.add_field(name="Timestamp", value=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                await log_channel.send(embed=embed)
                
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to ban this member.")
        except Exception as e:
            await ctx.send(f"❌ Error banning member: {str(e)}")

    @commands.command(name="unban")
    async def unban_member(self, ctx, user_input, *, reason=None):
        """Unban a user from the server.
        
        You must use a user ID (e.g., 1234567890).
        """
        if not user_input.isdigit():
            return await ctx.send("❌ Please provide a valid user ID to unban.")
        
        user_id = int(user_input)
        
        # Get ban list and check if user is banned
        bans = await ctx.guild.bans()
        banned_user = None
        
        for ban_entry in bans:
            if ban_entry.user.id == user_id:
                banned_user = ban_entry.user
                break
        
        if not banned_user:
            return await ctx.send(f"❌ User with ID {user_id} is not banned.")
        
        # Confirm before unbanning
        confirm_msg = f"Are you sure you want to unban {banned_user.name}#{banned_user.discriminator} [ID: {banned_user.id}]?"
        if reason:
            confirm_msg += f"\nReason: {reason}"
        confirm_msg += "\nRespond with 'yes' to confirm or 'no' to cancel."
        
        await ctx.send(confirm_msg)
        
        # Wait for confirmation
        try:
            response = await self.bot.wait_for(
                'message',
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no'],
                timeout=30.0
            )
            
            if response.content.lower() == 'no':
                return await ctx.send("✅ Unban cancelled.")
            
        except asyncio.TimeoutError:
            return await ctx.send("⏱️ Unban cancelled due to timeout.")
        
        # Perform the unban
        try:
            await ctx.guild.unban(banned_user, reason=reason)
            await ctx.send(f"✅ {banned_user.name}#{banned_user.discriminator} [ID: {banned_user.id}] has been unbanned.")
            
            # Log the action
            log_channel = discord.utils.get(ctx.guild.text_channels, name='mod-logs')
            if log_channel:
                embed = discord.Embed(
                    title="User Unbanned",
                    description=f"User {banned_user.name}#{banned_user.discriminator} was unbanned by {ctx.author.mention}",
                    color=discord.Color.green()
                )
                embed.add_field(name="Reason", value=reason or "No reason provided")
                embed.add_field(name="User ID", value=banned_user.id)
                embed.add_field(name="Timestamp", value=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                await log_channel.send(embed=embed)
                
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to unban users.")
        except Exception as e:
            await ctx.send(f"❌ Error unbanning user: {str(e)}")

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
