# Imports
import os
import os.path
import psutil
import json
import time
import datetime
import discord
import asyncio
import random
import praw
import api.auth
import utils.logger
import utils.ping
from framework import *
from math import floor
from random import randint
import framework.isobot.currency
import framework.isobot.colors
import framework.isobank.authorize
import framework.isobank.manager
import framework.isobot.embedengine
from discord import ApplicationContext, option
from discord.ext import commands
from discord.ext.commands import *
from cogs.economy import get_wallet, get_bank, new_bank, new_wallet

# Slash option types:
# Just use variable types to define option types.
# For example, if the option has to be only str:
# @option(name="something", description="A description", type=str)

#Variables
client = discord.Bot()
color = discord.Color.random()
wdir = os.getcwd()
reddit = praw.Reddit(client_id='_pazwWZHi9JldA', client_secret='1tq1HM7UMEGIro6LlwtlmQYJ1jB4vQ', user_agent='idk', check_for_async=False)
with open('database/warnings.json', 'r') as f: warnings = json.load(f)
with open('database/items.json', 'r') as f: items = json.load(f)
with open('config/shop.json', 'r') as f: shopitem = json.load(f)
with open('database/presence.json', 'r') as f: presence = json.load(f)
with open('database/levels.json', 'r') as f: levels = json.load(f)
with open('config/commands.json', 'r') as f: commandsdb = json.load(f)
with open('database/automod.json', 'r') as f: automod_config = json.load(f)
with open('database/isotokens.json', 'r') as f: isocoins = json.load(f)

#Pre-Initialization Commands
def timenow(): datetime.datetime.now().strftime("%H:%M:%S")
def save():
    with open('database/warnings.json', 'w+') as f: json.dump(warnings, f, indent=4)
    with open('database/items.json', 'w+') as f: json.dump(items, f, indent=4)
    with open('database/presence.json', 'w+') as f: json.dump(presence, f, indent=4)
    with open('database/levels.json', 'w+') as f: json.dump(levels, f, indent=4)
    with open('database/automod.json', 'w+') as f: json.dump(automod_config, f, indent=4)
    with open('database/isotokens.json', 'w+') as f: json.dump(isocoins, f, indent=4)

def get_user_networth(user_id:int):
    nw = get_wallet(user_id) + get_bank(user_id)
    #for e in items[str(user_id)]:
    #    if e != 0: nw += shopitem[e]["sell price"]
    return nw

if not os.path.isdir("logs"):
    os.mkdir('logs')
    try:
        open('logs/info-log.txt', 'x')
        utils.logger.info("Created info log", nolog=True)
        time.sleep(0.5)
        open('logs/error-log.txt', 'x')
        utils.logger.info("Created error log", nolog=True)
        time.sleep(0.5)
        open('logs/currency.log', 'x')
        utils.logger.info("Created currency log", nolog=True)
    except Exception as e: utils.logger.error(f"Failed to make log file: {e}", nolog=True)

#Classes
class plugins:
    economy = True
    moderation = True
    levelling = False
    music = False

class ShopData:
    def __init__(self, db_path: str):
        self.db_path = db_path 
        with open(db_path, 'r') as f: self.config = json.load(f)
        
    def get_item_ids(self) -> list:
        json_list = list()
        for h in self.config: json_list.append(str(h))
        return json_list
    
    def get_item_names(self) -> list:
        json_list = list()
        for h in self.config: json_list.append(str(h["stylized name"]))
        return json_list

#Framework Module Loader
colors = framework.isobot.colors.Colors()
currency_unused = framework.isobot.currency.CurrencyAPI(f'{wdir}/database/currency.json', f"{wdir}/logs/currency.log")  # Initialize part of the framework (Currency)
# isobank = framework.isobank.manager.IsoBankManager(f"{wdir}/database/isobank/accounts.json", f"{wdir}/database/isobank/auth.json")
isobankauth = framework.isobank.authorize.IsobankAuth(f"{wdir}/database/isobank/auth.json", f"{wdir}/database/isobank/accounts.json")
shop_data = ShopData(f"{wdir}/config/shop.json")

all_item_ids = shop_data.get_item_ids()

#Theme Loader
with open("themes/halloween.theme.json", 'r') as f:
    theme = json.load(f)
    try:
        color_loaded = theme["theme"]["embed_color"]
        color = int(color_loaded, 16)
    except KeyError:
        print(f"{colors.red}The theme file being loaded might be broken. Rolling back to default configuration...{colors.end}")
        color = discord.Color.random()

#Events
@client.event
async def on_ready():
    print("""
Isobot  Copyright (C) 2022  PyBotDevs/NKA
This program comes with ABSOLUTELY NO WARRANTY; for details run `/w'.
This is free software, and you are welcome to redistribute it
under certain conditions; run `/c' for details.
__________________________________________________""")
    time.sleep(2)
    print(f'Logged in as {client.user.name}.')
    print('Ready to accept commands.')
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="GitHub"), status=discord.Status.idle)
    print(f'[main/LOG] {colors.green}Status set to IDLE. Rich presence set.{colors.end}')
    print("[main/FLASK] Starting pinger service...")
    utils.ping.host()
    time.sleep(5)

@client.event
async def on_message(ctx):
    new_wallet(ctx.author.id)
    new_bank(ctx.author.id)
    if str(ctx.author.id) not in isocoins: isocoins[str(ctx.author.id)] = 0
    if str(ctx.guild.id) not in warnings: warnings[str(ctx.guild.id)] = {}
    if str(ctx.author.id) not in warnings[str(ctx.guild.id)]: warnings[str(ctx.guild.id)][str(ctx.author.id)] = []
    if str(ctx.author.id) not in items: items[str(ctx.author.id)] = {}
    if str(ctx.author.id) not in levels: levels[str(ctx.author.id)] = {"xp": 0, "level": 0}
    if str(ctx.guild.id) not in automod_config: automod_config[str(ctx.guild.id)] = \
    {
        "swear_filter": {
            "enabled": False,
            "keywords": {
                "use_default": True,
                "default": ["fuck", "shit", "pussy", "penis", "cock", "vagina", "sex", "moan", "bitch", "hoe", "nigga", "nigger", "xxx", "porn"],
                "custom": []
            }
        }
    }
    for z in shopitem:
        if z in items[str(ctx.author.id)]: pass
        else: items[str(ctx.author.id)][str(z)] = 0
    save()
    uList = list()
    if str(ctx.guild.id) in presence:
        for x in presence[str(ctx.guild.id)].keys(): uList.append(x)
    else: pass
    for i in uList:
        if i in ctx.content and not ctx.author.bot:
            fetch_user = client.get_user(id(i))
            await ctx.channel.send(f"{fetch_user.display_name} went AFK <t:{floor(presence[str(ctx.guild.id)][str(i)]['time'])}:R>: {presence[str(ctx.guild.id)][str(i)]['response']}")
    if str(ctx.guild.id) in presence and str(ctx.author.id) in presence[str(ctx.guild.id)]:
        del presence[str(ctx.guild.id)][str(ctx.author.id)]
        save()
        m1 = await ctx.channel.send(f"Welcome back {ctx.author.mention}. Your AFK has been removed.")
        await asyncio.sleep(5)
        await m1.delete()
    if not ctx.author.bot:
        levels[str(ctx.author.id)]["xp"] += randint(1, 5)
        xpreq = 0
        for level in range(int(levels[str(ctx.author.id)]["level"])):
            xpreq += 50
            if xpreq >= 5000: break
        if levels[str(ctx.author.id)]["xp"] >= xpreq:
            levels[str(ctx.author.id)]["xp"] = 0
            levels[str(ctx.author.id)]["level"] += 1
            await ctx.author.send(f"{ctx.author.mention}, you just ranked up to **level {levels[str(ctx.author.id)]['level']}**. Nice!")
        save()
        if automod_config[str(ctx.guild.id)]["swear_filter"]["enabled"] == True:
            if automod_config[str(ctx.guild.id)]["swear_filter"]["keywords"]["use_default"] and any(x in ctx.content.lower() for x in automod_config[str(ctx.guild.id)]["swear_filter"]["keywords"]["default"]):
                await ctx.delete()
                await ctx.channel.send(f'{ctx.author.mention} watch your language.', delete_after=5)
            elif automod_config[str(ctx.guild.id)]["swear_filter"]["keywords"]["custom"] is not [] and any(x in ctx.content.lower() for x in automod_config[str(ctx.guild.id)]["swear_filter"]["keywords"]["custom"]):
                await ctx.delete()
                await ctx.channel.send(f'{ctx.author.mention} watch your language.', delete_after=5)

#Error handler
@client.event
async def on_application_command_error(ctx: ApplicationContext, error: discord.DiscordException):
    current_time = datetime.time().strftime("%H:%M:%S")
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.channel.send(f':stopwatch: Not now! Please try after **{str(datetime.timedelta(seconds=int(round(error.retry_after))))}**')
        print(f'[{current_time}] Ignoring exception at {colors.cyan}CommandOnCooldown{colors.end}. Details: This command is currently on cooldown.')
    elif isinstance(error, commands.MissingPermissions):
        await ctx.channel.send('You don\'t have permission to do this!', ephemeral=True)
        print(f'[{current_time}] Ignoring exception at {colors.cyan}MissingPermissions{colors.end}. Details: The user doesn\'t have the required permissions.')
    elif isinstance(error, commands.BadArgument):
        await ctx.channel.send(':x: Invalid argument.', delete_after=8)
        print(f'[{current_time}] Ignoring exception at {colors.cyan}BadArgument{colors.end}.')
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.channel.send(':x: I don\'t have the required permissions to use this.')
        print(f'[{current_time}] Ignoring exception at {colors.cyan}BotMissingPremissions{colors.end}. Details: The bot doesn\'t have the required permissions.')
    elif isinstance(error, commands.BadBoolArgument):
        await ctx.channel.send(':x: Invalid true/false argument.', delete_after=8)
        print(f'[{current_time}] Ignoring exception at {colors.cyan}BadBoolArgument{colors.end}.')

#Commands
@client.slash_command(
    name="help",
    description="Gives you help with a specific command, or shows a list of all commands"
)
@option(name="command", description="Which command do you need help with?", type=str, default=None)
async def help(ctx: ApplicationContext, command:str=None):
    if command is not None:
        try:
            localembed = discord.Embed(title=f"{commandsdb[command]['name']} Command (/{command})", description=commandsdb[command]['description'], color=color)
            localembed.add_field(name="Command Type", value=commandsdb[command]['type'], inline=False)
            if commandsdb[command]['cooldown'] is not None: localembed.add_field(name="Cooldown", value=f"{str(datetime.timedelta(seconds=commandsdb[command]['cooldown']))}", inline=False)
            localembed.add_field(name="Usable By", value=commandsdb[command]['usable_by'], inline=False)
            if commandsdb[command]['args'] is not None:
                r = ""
                for x in commandsdb[command]['args']: r += f"`{x}` "
                localembed.add_field(name="Arguments", value=r, inline=False)
            if commandsdb[command]['bugged'] == True: localembed.set_footer(text="⚠ This command might be bugged (experiencing issues), but will be fixed later.")
            if commandsdb[command]['disabled'] == True: localembed.set_footer(text="⚠ This command is currently disabled")
            await ctx.respond(embed=localembed)
        except KeyError: return await ctx.respond(embed=discord.Embed(description=f"No results found for {command}."), ephemeral=True)
    else:
        r = ""
        for x in commandsdb: 
            if commandsdb[x]["type"] != "DevTools": r += f"`/{x}`\n"
        localembed = discord.Embed(title="Isobot Command Help", description=f"**Bot Commands:**\n{r}", color = color)
        user = client.fetch_user(ctx.author.id)
        await user.send(embed=localembed)
        await ctx.respond("Check your direct messages.", ephemeral=True)

@client.slash_command(
    name='whoami',
    description='Shows information on a user'
)
@option(name="user", description="Who do you want to know about?", type=discord.User, default=None)
async def whoami(ctx: ApplicationContext, user: discord.User=None):
    if user == None: user = ctx.author
    username = user
    displayname = user.display_name
    registered = user.joined_at.strftime("%b %d, %Y, %T")
    pfp = user.avatar
    localembed_desc = f"`AKA` {displayname}"
    if str(user.id) in presence[str(ctx.guild.id)]: localembed_desc += f"\n`🌙 AFK` {presence[str(ctx.guild.id)][str(user.id)]['response']} - <t:{floor(presence[str(ctx.guild.id)][str(user.id)]['time'])}>"
    localembed = discord.Embed(
        title=f'User Info on {username}', 
        description=localembed_desc
    )
    localembed.set_thumbnail(url=pfp)
    localembed.add_field(name='Username', value=username, inline=True)
    localembed.add_field(name='Display Name', value=displayname, inline=True)
    localembed.add_field(name='Joined Discord on', value=registered, inline=False)
    localembed.add_field(name='Avatar URL', value=f"[here!]({pfp})", inline=True)
    role_render = ""
    for p in user.roles:
        if p != user.roles[0]: role_render += f"<@&{p.id}> "
    localembed.add_field(name='Roles', value=role_render, inline=False)
    localembed.add_field(name="Net worth", value=f"{get_user_networth(user.id)} coins", inline=False)
    await ctx.respond(embed=localembed)

# DevTools commands
@client.slash_command(
    name='sync',
    description='Syncs all of the local databases with their latest version'
)
async def sync(ctx: ApplicationContext):
    if ctx.author.id != 738290097170153472: return await ctx.respond('Sorry, this command is only for my developer\'s use.')
    try:
        with open('database/warnings.json', 'r') as f: warnings = json.load(f)
        with open('database/items.json', 'r') as f: items = json.load(f)
        with open('config/shop.json', 'r') as f: shopitem = json.load(f)
        await ctx.respond('Databases resynced.', ephemeral=True)
    except Exception as e:
        print(e)
        await ctx.respond('An error occured while resyncing. Check console.', ephemeral=True)

@client.slash_command(
    name='prediction',
    description='Randomly predicts a yes/no question.'
)
@option(name="question", description="What do you want to predict?", type=str)
async def prediction(ctx: ApplicationContext, question:str): await ctx.respond(f"My prediction is... **{random.choice(['Yes', 'No'])}!**")

# Cog Commands (these cannot be moved into a cog)
cogs = client.create_group("cog", "Commands for working with isobot cogs.")

@cogs.command(
    name="load",
    description="Loads a cog."
)
@option(name="cog", description="What cog do you want to load?", type=str)
async def load(ctx: ApplicationContext, cog: str):
    if ctx.author.id != 738290097170153472: return await ctx.respond("You can't use this command!", ephemeral=True)
    try:
        client.load_extension(f"cogs.{cog}")
        await ctx.respond(embed=discord.Embed(description=f"{cog} cog successfully loaded.", color=discord.Color.green()))
    except Exception as e: await ctx.respond(embed=discord.Embed(description=f"{cog} failed to load: {e}", color=discord.Color.red()))

@cogs.command(
    name="disable",
    description="Disables a cog."
)
@option(name="cog", description="What cog do you want to disable?", type=str)
async def disable(ctx: ApplicationContext, cog: str):
    if ctx.author.id != 738290097170153472: return await ctx.respond("You can't use this command!", ephemeral=True)
    try:
        client.unload_extension(f"cogs.{cog}")
        await ctx.respond(embed=discord.Embed(description=f"{cog} cog successfully disabled.", color=discord.Color.green()))
    except: await ctx.respond(embed=discord.Embed(description=f"{cog} cog not found."), color=discord.Color.red())

@cogs.command(
    name="reload",
    description="Reloads a cog."
)
@option(name="cog", description="What cog do you want to reload?", type=str)
async def reload(ctx: ApplicationContext, cog: str):
    if ctx.author.id != 738290097170153472: return await ctx.respond("You can't use this command!", ephemeral=True)
    try:
        client.reload_extension(f"cogs.{cog}")
        await ctx.respond(embed=discord.Embed(description=f"{cog} cog successfully reloaded.", color=discord.Color.green()))
    except: await ctx.respond(embed=discord.Embed(description=f"{cog} cog not found.", color=discord.Color.red()))

# IsoCoins commands
isocoin_system = client.create_group("isocoin", "Commands related to the IsoCoin rewards system.")

isocoin_system.command(
    name="balance",
    description="See your IsoCoin balances"
)
async def isocoin_balance(ctx: ApplicationContext):
    localembed = discord.Embed(description=f"You currently have **{isocoins[str(ctx.author.id)]}** IsoCoins.")
    await ctx.respond(embed=localembed)

isocoin_system.command(
    name="daily",
    description="Collect your daily reward of IsoCoins"
)
@commands.cooldown(1, 86400, commands.BucketType.user)
async def isocoin_daily(ctx: ApplicationContext):
    isocoins_reward = random.randint(2500, 5000)
    isocoins[str(ctx.author.id)] += isocoins_reward
    save()
    await ctx.respond(f"You have earned {isocoins_reward} IsoCoins from this daily. Come back in 24 hours for the next one!")

isocoin_system.command(
    name="shop",
    description="See all the items that you can buy using your IsoCoins."
)
async def isocoin_shop(ctx: ApplicationContext):
    await ctx.respond("IsoCoin shop is coming soon! Check back later for new items.")

# Initialization
active_cogs = ["economy", "maths", "moderation", "reddit", "minigames", "automod", "isobank", "levelling", "fun", "afk"]
i = 1
cog_errors = 0
for x in active_cogs:
    print(f"[main/Cogs] Loading isobot Cog ({i}/{len(active_cogs)})")
    i += 1
    try: client.load_extension(f"cogs.{x}")
    except Exception as e:
        cog_errors += 1 
        print(f"[main/Cogs] {colors.red}ERROR: Cog \"{x}\" failed to load: {e}{colors.end}")
if cog_errors == 0: print(f"[main/Cogs] {colors.green}All cogs successfully loaded.{colors.end}")
else: print(f"[main/Cogs] {colors.yellow}{cog_errors}/{len(active_cogs)} cogs failed to load.{colors.end}")
print("--------------------")
if api.auth.get_mode(): 
    print(f"[main/CLIENT] Starting client in {colors.cyan}Replit mode{colors.end}...")
    client.run(os.getenv("TOKEN"))
else:
    print(f"[main/CLIENT] Starting client in {colors.orange}local mode{colors.end}...") 
    client.run(api.auth.get_token())




# btw i use arch
