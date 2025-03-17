import discord
from discord.ext import commands
import config
from datetime import datetime
import json
import os

class Roles(commands.Cog):
    """Role management commands."""

    def __init__(self, bot):
        self.bot = bot
        self.roles_data_file = "roles_data.json"
        self.roles_data = self.load_roles_data()
        
        # Role emoji mappings
        self.role_emojis = {
            "📈": "Trader",
            "💎": "HODLer",
            "📊": "Analyst",
            "💻": "Developer",
            "💰": "Investor"
        }

    def load_roles_data(self):
        """Load roles data from file or create default data structure."""
        if os.path.exists(self.roles_data_file):
            try:
                with open(self.roles_data_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading roles data file: {e}")
                return {"roles_message_id": 0}
        else:
            return {"roles_message_id": 0}
            
    def save_roles_data(self):
        """Save roles data to file."""
        try:
            with open(self.roles_data_file, 'w') as f:
                json.dump(self.roles_data, f, indent=4)
        except Exception as e:
            print(f"Error saving roles data file: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Event triggered when a reaction is added to a message."""
        # Skip if it's the bot's own reaction
        if payload.user_id == self.bot.user.id:
            return
            
        # Check if reaction was added to the roles message
        if payload.message_id == self.roles_data.get("roles_message_id", 0):
            emoji = str(payload.emoji)
            
            # Check if this emoji is mapped to a role
            if emoji in self.role_emojis:
                guild = self.bot.get_guild(payload.guild_id)
                if not guild:
                    return
                
                member = guild.get_member(payload.user_id)
                if not member or member.bot:
                    return
                
                # Get the role
                role_name = self.role_emojis[emoji]
                role = discord.utils.get(guild.roles, name=role_name)
                
                if role:
                    try:
                        await member.add_roles(role)
                        # Try to send a DM
                        try:
                            await member.send(f"You have been given the **{role_name}** role in **{guild.name}**!")
                        except discord.Forbidden:
                            pass
                    except Exception as e:
                        print(f"Error adding role: {e}")
                        
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Event triggered when a reaction is removed from a message."""
        # Check if reaction was removed from the roles message
        if payload.message_id == self.roles_data.get("roles_message_id", 0):
            emoji = str(payload.emoji)
            
            # Check if this emoji is mapped to a role
            if emoji in self.role_emojis:
                guild = self.bot.get_guild(payload.guild_id)
                if not guild:
                    return
                
                member = guild.get_member(payload.user_id)
                if not member or member.bot:
                    return
                
                # Get the role
                role_name = self.role_emojis[emoji]
                role = discord.utils.get(guild.roles, name=role_name)
                
                if role:
                    try:
                        await member.remove_roles(role)
                    except Exception as e:
                        print(f"Error removing role: {e}")

    @commands.command(name="getrole")
    async def getrole(self, ctx, *, role_name=None):
        """Assign a self-assignable role to yourself."""
        if role_name is None:
            # List available roles
            available_roles = ", ".join(f"`{role}`" for role in config.SELF_ASSIGNABLE_ROLES.values())
            embed = discord.Embed(
                title="Available Self-Assignable Roles",
                description=f"Use `{config.PREFIX}getrole <role>` to assign yourself a role.\nAvailable roles: {available_roles}",
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed)
        
        # Check if the role is self-assignable
        role_id = None
        for key, value in config.SELF_ASSIGNABLE_ROLES.items():
            if value.lower() == role_name.lower():
                role_id = key
                role_name = value
                break
        
        if role_id is None:
            # Try to match role name directly
            for key, value in config.SELF_ASSIGNABLE_ROLES.items():
                if key.lower() == role_name.lower():
                    role_id = key
                    role_name = value
                    break
        
        if role_id is None:
            return await ctx.send(f"❌ `{role_name}` is not a self-assignable role. Use `{config.PREFIX}getrole` to see available roles.")
        
        # Find the role
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role is None:
            return await ctx.send(f"❌ Role `{role_name}` doesn't exist on this server. Please contact an administrator.")
        
        # Add the role to the user
        if role in ctx.author.roles:
            await ctx.author.remove_roles(role)
            await ctx.send(f"✅ Removed role `{role.name}` from you.")
        else:
            await ctx.author.add_roles(role)
            await ctx.send(f"✅ Added role `{role.name}` to you.")

    @commands.command(name="roles_message")
    @commands.has_permissions(administrator=True)
    async def create_roles_message(self, ctx):
        """Creates a beautifully formatted message for role selection with reactions."""
        roles_channel = self.bot.get_channel(config.ROLES_CHANNEL_ID)
        
        if not roles_channel:
            return await ctx.send("❌ Roles channel not found. Please set it up in config.")
        
        embed = discord.Embed(
            title="🎭 XGC Trenches Role Selection",
            description=(
                "Choose roles that match your interests and expertise in the XRP & crypto world!\n\n"
                "**React with the emoji next to the role you want to assign yourself:**"
            ),
            color=0x5865F2,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📈 Trader",
            value=(
                "For active traders who buy and sell regularly.\n"
                "React with 📈 to get this role"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💎 HODLer",
            value=(
                "Long-term believers in XRP and crypto. Diamond hands!\n"
                "React with 💎 to get this role"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📊 Analyst",
            value=(
                "Technical and fundamental analysts who study the markets.\n"
                "React with 📊 to get this role"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💻 Developer",
            value=(
                "Blockchain and software developers building on XRP Ledger.\n"
                "React with 💻 to get this role"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💰 Investor",
            value=(
                "Serious investors focused on building portfolio value.\n"
                "React with 💰 to get this role"
            ),
            inline=False
        )
        
        embed.set_footer(text="XGC Trenches XRPL | React to get a role, remove your reaction to remove the role")
        
        # Send the embed to the roles channel
        roles_message = await roles_channel.send(embed=embed)
        
        # Save the message ID for reaction tracking
        self.roles_data["roles_message_id"] = roles_message.id
        self.save_roles_data()
        
        # Add the reactions
        for emoji in self.role_emojis.keys():
            await roles_message.add_reaction(emoji)
        
        await ctx.send("✅ Roles message has been posted in the roles channel with reaction options!")

async def setup(bot):
    await bot.add_cog(Roles(bot))
