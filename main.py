import asyncio
import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
intents.moderation = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
  print(f"Logged in as {bot.user.name}")


@bot.command(name="autoban")
@commands.has_permissions(ban_members=True, view_audit_log=True)
async def auto_ban(ctx, limit: int = 150):
  """Bans recent members/raiders automatically up to a specified limit or rate limit."""
  await ctx.message.delete()
  status_msg = await ctx.send(
      f"🛡️ Scanning and banning up to {limit} recent members..."
  )

  banned_count = 0
  failed_count = 0

  try:
    async for member in ctx.guild.fetch_members(limit=limit):
      if member.id == bot.user.id or member.guild_permissions.administrator:
        continue

      try:
        await ctx.guild.ban(
            member, reason="Raid protection - Auto ban", delete_message_days=1
        )
        banned_count += 1
        await asyncio.sleep(0.5)

      except discord.HTTPException as e:
        if e.status == 429:
          await ctx.send(
              "⚠️ Hit a Discord Rate Limit (429). Pausing operation.",
              delete_after=15,
          )
          break
        else:
          failed_count += 1

    await status_msg.edit(
        content=(
            f"✅ Auto-ban finished.\nSuccessfully banned: **{banned_count}**"
            f" users.\nFailed/Skipped: **{failed_count}**"
        )
    )

  except Exception as ex:
    await ctx.send(f"❌ An error occurred: {ex}")


# Pulls the token safely from Render's environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
  raise ValueError("❌ DISCORD_TOKEN environment variable not found!")

bot.run(TOKEN)
