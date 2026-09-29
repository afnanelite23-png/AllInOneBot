import os
import asyncio
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# --- KEEP-ALIVE SERVER FOR RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "DM Announcement Bot is operational!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Required to fetch all server members

bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

# --- CUSTOM HELP COMMAND ---
@bot.hybrid_command(name="help", description="Shows available commands.")
async def help_command(ctx):
    embed = discord.Embed(
        title="🤖 Announcement Bot Commands",
        description="Commands available for server administrators:",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📢 Announcements",
        value="`>dmall ` or `/dmall ` - Broadcast a DM to all server members.\n"
              "`>ping` or `/ping` - Check bot latency.\n"
              "`>help` or `/help` - Show this menu.",
        inline=False
    )
    embed.set_footer(text="Bot Owner announcement")
    await ctx.send(embed=embed)

# --- UTILITIES ---
@bot.hybrid_command(name="ping", description="Check bot latency")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latency: `{latency}ms`")

# --- DM ALL COMMAND ---
@bot.hybrid_command(name="dmall", description="Send a direct message to all server members (Admins only).")
@commands.has_permissions(administrator=True)
async def dmall(ctx, *, message: str):
    await ctx.defer()  # Prevents interaction timeout for slash commands
    
    successful = 0
    failed = 0

    embed = discord.Embed(
        title=f"📢 Announcement from {ctx.guild.name}",
        description=message,
        color=discord.Color.gold()
    )
    embed.set_footer(text="Bot Owner announcement")

    # Initial status response
    status_msg = await ctx.send(f"⏳ Starting DM broadcast to **{len(ctx.guild.members)}** members...")

    for member in ctx.guild.members:
        # Skip bots
        if member.bot:
            continue

        try:
            await member.send(embed=embed)
            successful += 1
            # 1.5 second delay between DMs to avoid Discord API rate-limits
            await asyncio.sleep(1.5)
        except Exception:
            # Triggers if the user has DMs closed or has blocked the bot
            failed += 1

    await status_msg.edit(content=f"✅ **DM Broadcast Completed!**\n- **Successfully sent:** `{successful}`\n- **Failed (DMs closed/blocked):** `{failed}`")

# --- ERROR HANDLING ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You do not have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Please provide a message to send! Example: `>dmall Hello everyone!`")

# --- START BOT ---
bot.run(os.getenv('DISCORD_TOKEN'))
