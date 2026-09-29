import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# --- KEEP-ALIVE SERVER FOR RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "All-in-One Bot is operational!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# --- BOT SETUP ---
intents = discord.Intents.all()
# Set help_command=None to disable default text help menu
bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)

# Simple in-memory balance tracker (resets on restart)
balances = {}

@bot.event
async def on_ready():
    # Sync slash commands globally across all servers
    await bot.tree.sync()
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

# --- CUSTOM HELP COMMAND ---
@bot.hybrid_command(name="help", description="Shows a list of all available commands.")
async def help_command(ctx):
    embed = discord.Embed(
        title="🤖 All-In-One Bot Commands",
        description="Here is a list of commands you can use with prefix `>` or slash `/`:",
        color=discord.Color.blue()
    )

    # Utilities Category
    embed.add_field(
        name="🛠️ Utilities",
        value="`>ping` or `/ping` - Check bot latency\n"
              "`>userinfo [@user]` or `/userinfo` - Get user details\n"
              "`>help` or `/help` - Show this menu",
        inline=False
    )

    # Moderation Category
    embed.add_field(
        name="🛡️ Moderation",
        value="`>kick <@user> [reason]` - Kick a member\n"
              "`>ban <@user> [reason]` - Ban a member\n"
              "`>clear ` - Purge messages from channel",
        inline=False
    )

    # Economy Category
    embed.add_field(
        name="💰 Economy",
        value="`>balance [@user]` - Check wallet balance\n"
              "`>work` - Work to earn coins (60s cooldown)",
        inline=False
    )

    embed.set_footer(text="Custom Bot Services by @plzdie")
    await ctx.send(embed=embed)

# --- UTILITIES ---
@bot.hybrid_command(name="ping", description="Check bot latency")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latency: `{latency}ms`")

@bot.hybrid_command(name="userinfo", description="Get info about a server member")
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"User Info - {member.name}", color=discord.Color.blue())
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
    await ctx.send(embed=embed)

# --- MODERATION ---
@bot.hybrid_command(name="kick", description="Kick a member from the server")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(f"✅ Kicked `{member.name}` | Reason: {reason}")

@bot.hybrid_command(name="ban", description="Ban a member from the server")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(f"⛔ Banned `{member.name}` | Reason: {reason}")

@bot.hybrid_command(name="clear", description="Purge messages from a channel")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Cleared `{len(deleted)-1}` messages.", delete_after=3)

# --- ECONOMY ---
@bot.hybrid_command(name="balance", description="Check account balance")
async def balance(ctx, member: discord.Member = None):
    user = member or ctx.author
    bal = balances.get(user.id, 100)  # Starting balance: 100
    await ctx.send(f"💰 {user.mention} has **${bal}** coins.")

@bot.hybrid_command(name="work", description="Work to earn coins")
@commands.cooldown(1, 60, commands.BucketType.user)  # 60-second cooldown
async def work(ctx):
    earned = 50
    balances[ctx.author.id] = balances.get(ctx.author.id, 100) + earned
    await ctx.send(f"💼 You worked hard and earned **${earned}** coins!")

# --- ERROR HANDLING ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You do not have permission to use this command.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Cooldown active. Try again in {round(error.retry_after, 1)} seconds.")

# --- START BOT ---
bot.run(os.getenv('DISCORD_TOKEN'))
