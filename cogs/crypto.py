import discord
from discord.ext import commands
import aiohttp
import json
import config
from datetime import datetime
import asyncio

class Crypto(commands.Cog):
    """Cryptocurrency information commands"""

    def __init__(self, bot):
        self.bot = bot
        # XGC token info
        self.XGC_ISSUER = "rM4qkDcRyMDks5v1hYakKnLbTeppmgCpM1"
        self.XGC_CURRENCY = "XGC"
        
    @commands.command(name="xgcprice")
    async def xgc_price(self, ctx):
        """Get the current price of XGC in XRP from the XRP Ledger"""
        
        embed = discord.Embed(
            title="Fetching XGC Price...",
            description="Querying the XRP Ledger for the latest XGC price...",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        message = await ctx.send(embed=embed)
        
        try:
            # Query the XRP Ledger using JSON-RPC API
            async with aiohttp.ClientSession() as session:
                # Use public XRP Ledger node
                url = "https://s1.ripple.com:51234/"
                
                # Query the XGC/XRP order book
                payload = {
                    "method": "book_offers",
                    "params": [{
                        "taker_gets": {
                            "currency": "XRP"
                        },
                        "taker_pays": {
                            "currency": self.XGC_CURRENCY,
                            "issuer": self.XGC_ISSUER
                        },
                        "limit": 10
                    }]
                }
                
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check if we have offers
                        if "result" in data and "offers" in data["result"] and len(data["result"]["offers"]) > 0:
                            # Get the best offer
                            best_offer = data["result"]["offers"][0]
                            
                            # Extract values and calculate price
                            xrp_amount = float(best_offer["TakerGets"]) / 1_000_000  # Convert drops to XRP
                            xgc_amount = float(best_offer["TakerPays"]["value"])
                            xgc_price_in_xrp = xrp_amount / xgc_amount
                            
                            # Create success embed
                            embed = discord.Embed(
                                title="XGC Price",
                                description=f"Current price from the XRP Ledger DEX",
                                color=discord.Color.green(),
                                timestamp=datetime.utcnow()
                            )
                            
                            embed.add_field(
                                name="XGC/XRP",
                                value=f"**{xgc_price_in_xrp:.6f} XRP**",
                                inline=False
                            )
                            
                            # Add some extra info about the data
                            embed.add_field(
                                name="Trade Details",
                                value=f"Best offer: {xrp_amount:.2f} XRP for {xgc_amount:.2f} XGC",
                                inline=True
                            )
                            
                            embed.add_field(
                                name="Data Source",
                                value="XRP Ledger DEX",
                                inline=True
                            )
                            
                            embed.set_footer(text=f"Requested by {ctx.author.display_name}")
                            
                            await message.edit(embed=embed)
                        else:
                            await message.edit(embed=discord.Embed(
                                title="XGC Price Not Available",
                                description="No offers found for XGC/XRP on the XRP Ledger DEX.",
                                color=discord.Color.red(),
                                timestamp=datetime.utcnow()
                            ))
                    else:
                        await message.edit(embed=discord.Embed(
                            title="Error",
                            description=f"Failed to fetch data from XRP Ledger: HTTP {response.status}",
                            color=discord.Color.red(),
                            timestamp=datetime.utcnow()
                        ))
                        
        except Exception as e:
            await message.edit(embed=discord.Embed(
                title="Error",
                description=f"An error occurred while fetching XGC price: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            ))
            
    @commands.command(name="xrpprice")
    async def xrp_price(self, ctx):
        """Get the current price of XRP in USD from the XRP Ledger"""
        
        embed = discord.Embed(
            title="Fetching XRP Price...",
            description="Querying the XRP Ledger for the latest XRP price...",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        message = await ctx.send(embed=embed)
        
        try:
            # Query the XRP Ledger using JSON-RPC API
            async with aiohttp.ClientSession() as session:
                # Use public XRP Ledger node
                url = "https://s1.ripple.com:51234/"
                
                # Bitstamp's USD issuer address
                USD_ISSUER = "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B"
                
                # Query the XRP/USD order book
                payload = {
                    "method": "book_offers",
                    "params": [{
                        "taker_gets": {
                            "currency": "USD",
                            "issuer": USD_ISSUER
                        },
                        "taker_pays": {
                            "currency": "XRP"
                        },
                        "limit": 10
                    }]
                }
                
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check if we have offers
                        if "result" in data and "offers" in data["result"] and len(data["result"]["offers"]) > 0:
                            # Get the best offer
                            best_offer = data["result"]["offers"][0]
                            
                            # Extract values and calculate price
                            usd_amount = float(best_offer["TakerGets"]["value"])
                            xrp_amount = float(best_offer["TakerPays"]) / 1_000_000  # Convert drops to XRP
                            xrp_price_in_usd = usd_amount / xrp_amount
                            
                            # Create success embed
                            embed = discord.Embed(
                                title="XRP Price",
                                description=f"Current price from the XRP Ledger DEX",
                                color=discord.Color.green(),
                                timestamp=datetime.utcnow()
                            )
                            
                            embed.add_field(
                                name="XRP/USD",
                                value=f"**${xrp_price_in_usd:.4f} USD**",
                                inline=False
                            )
                            
                            # Add some extra info about the data
                            embed.add_field(
                                name="Trade Details",
                                value=f"Best offer: ${usd_amount:.2f} USD for {xrp_amount:.2f} XRP",
                                inline=True
                            )
                            
                            embed.add_field(
                                name="Data Source",
                                value="XRP Ledger DEX (Bitstamp)",
                                inline=True
                            )
                            
                            embed.set_footer(text=f"Requested by {ctx.author.display_name}")
                            
                            await message.edit(embed=embed)
                        else:
                            await message.edit(embed=discord.Embed(
                                title="XRP Price Not Available",
                                description="No offers found for XRP/USD on the XRP Ledger DEX.",
                                color=discord.Color.red(),
                                timestamp=datetime.utcnow()
                            ))
                    else:
                        await message.edit(embed=discord.Embed(
                            title="Error",
                            description=f"Failed to fetch data from XRP Ledger: HTTP {response.status}",
                            color=discord.Color.red(),
                            timestamp=datetime.utcnow()
                        ))
                        
        except Exception as e:
            await message.edit(embed=discord.Embed(
                title="Error",
                description=f"An error occurred while fetching XRP price: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            ))
    
    @commands.command(name="xgcusd")
    async def xgc_price_usd(self, ctx):
        """Get the current price of XGC in USD (calculated via XGC/XRP and XRP/USD)"""
        
        embed = discord.Embed(
            title="Fetching XGC Price in USD...",
            description="Querying the XRP Ledger for the latest XGC price in USD...",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        message = await ctx.send(embed=embed)
        
        try:
            # Query the XRP Ledger using JSON-RPC API
            async with aiohttp.ClientSession() as session:
                # Use public XRP Ledger node
                url = "https://s1.ripple.com:51234/"
                
                # 1. Get XGC/XRP price
                xgc_xrp_payload = {
                    "method": "book_offers",
                    "params": [{
                        "taker_gets": {
                            "currency": "XRP"
                        },
                        "taker_pays": {
                            "currency": self.XGC_CURRENCY,
                            "issuer": self.XGC_ISSUER
                        },
                        "limit": 10
                    }]
                }
                
                # 2. Get XRP/USD price
                # Bitstamp's USD issuer address
                USD_ISSUER = "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B"
                
                xrp_usd_payload = {
                    "method": "book_offers",
                    "params": [{
                        "taker_gets": {
                            "currency": "USD",
                            "issuer": USD_ISSUER
                        },
                        "taker_pays": {
                            "currency": "XRP"
                        },
                        "limit": 10
                    }]
                }
                
                # First request - XGC/XRP
                async with session.post(url, json=xgc_xrp_payload) as xgc_xrp_response:
                    if xgc_xrp_response.status != 200:
                        await message.edit(embed=discord.Embed(
                            title="Error",
                            description=f"Failed to fetch XGC/XRP data: HTTP {xgc_xrp_response.status}",
                            color=discord.Color.red(),
                            timestamp=datetime.utcnow()
                        ))
                        return
                    
                    xgc_xrp_data = await xgc_xrp_response.json()
                    
                    # Check if we have offers
                    if "result" not in xgc_xrp_data or "offers" not in xgc_xrp_data["result"] or len(xgc_xrp_data["result"]["offers"]) == 0:
                        await message.edit(embed=discord.Embed(
                            title="XGC Price Not Available",
                            description="No offers found for XGC/XRP on the XRP Ledger DEX.",
                            color=discord.Color.red(),
                            timestamp=datetime.utcnow()
                        ))
                        return
                    
                    # Get the best offer
                    best_xgc_xrp_offer = xgc_xrp_data["result"]["offers"][0]
                    
                    # Extract values and calculate price
                    xrp_amount = float(best_xgc_xrp_offer["TakerGets"]) / 1_000_000  # Convert drops to XRP
                    xgc_amount = float(best_xgc_xrp_offer["TakerPays"]["value"])
                    xgc_price_in_xrp = xrp_amount / xgc_amount
                
                # Second request - XRP/USD
                async with session.post(url, json=xrp_usd_payload) as xrp_usd_response:
                    if xrp_usd_response.status != 200:
                        await message.edit(embed=discord.Embed(
                            title="Error",
                            description=f"Failed to fetch XRP/USD data: HTTP {xrp_usd_response.status}",
                            color=discord.Color.red(),
                            timestamp=datetime.utcnow()
                        ))
                        return
                    
                    xrp_usd_data = await xrp_usd_response.json()
                    
                    # Check if we have offers
                    if "result" not in xrp_usd_data or "offers" not in xrp_usd_data["result"] or len(xrp_usd_data["result"]["offers"]) == 0:
                        await message.edit(embed=discord.Embed(
                            title="XRP Price Not Available",
                            description="No offers found for XRP/USD on the XRP Ledger DEX.",
                            color=discord.Color.red(),
                            timestamp=datetime.utcnow()
                        ))
                        return
                    
                    # Get the best offer
                    best_xrp_usd_offer = xrp_usd_data["result"]["offers"][0]
                    
                    # Extract values and calculate price
                    usd_amount = float(best_xrp_usd_offer["TakerGets"]["value"])
                    xrp_for_usd = float(best_xrp_usd_offer["TakerPays"]) / 1_000_000  # Convert drops to XRP
                    xrp_price_in_usd = usd_amount / xrp_for_usd
                
                # Calculate XGC/USD price
                xgc_price_in_usd = xgc_price_in_xrp * xrp_price_in_usd
                
                # Create success embed
                embed = discord.Embed(
                    title="XGC Price in USD",
                    description=f"Current price calculated from the XRP Ledger DEX",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="XGC/USD",
                    value=f"**${xgc_price_in_usd:.6f} USD**",
                    inline=False
                )
                
                embed.add_field(
                    name="XGC/XRP",
                    value=f"**{xgc_price_in_xrp:.6f} XRP**",
                    inline=True
                )
                
                embed.add_field(
                    name="XRP/USD",
                    value=f"**${xrp_price_in_usd:.4f} USD**",
                    inline=True
                )
                
                embed.add_field(
                    name="Data Source",
                    value="XRP Ledger DEX (Bitstamp for USD)",
                    inline=False
                )
                
                embed.set_footer(text=f"Requested by {ctx.author.display_name}")
                
                await message.edit(embed=embed)
                        
        except Exception as e:
            await message.edit(embed=discord.Embed(
                title="Error",
                description=f"An error occurred while fetching XGC price: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            ))

    @commands.command(name="cryptodisclaimer")
    async def crypto_disclaimer(self, ctx):
        """Display cryptocurrency disclaimer"""
        embed = discord.Embed(
            title="Cryptocurrency Disclaimer",
            description="Important information about cryptocurrency discussions in this server",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Not Financial Advice",
            value="Information shared in this server is for educational and informational purposes only. It should not be considered financial or investment advice.",
            inline=False
        )
        
        embed.add_field(
            name="Risk Warning",
            value="Cryptocurrency investments are highly speculative and volatile. Never invest more than you can afford to lose.",
            inline=False
        )
        
        embed.add_field(
            name="DYOR",
            value="Always Do Your Own Research before making any investment decisions. Verify information from multiple sources.",
            inline=False
        )
        
        embed.add_field(
            name="No Pump and Dump",
            value="This server does not condone pump and dump schemes or any form of market manipulation.",
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Crypto(bot)) 