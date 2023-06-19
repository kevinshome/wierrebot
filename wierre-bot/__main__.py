# stopped on page 80
# 10/10/2022 5:42PM
import os
import random
import discord
from discord.ext.commands.bot import Bot
from dotenv import load_dotenv
from . import __version__

load_dotenv()
intents = discord.Intents.default()
bot = Bot(intents=intents)

global bars
global quotes
global quote_queue
global bar_queue

with open(os.path.join(os.path.dirname(__file__), "bars.txt"), 'r') as f:
    bars = [x.strip() for x in f.readlines()]
    bar_queue = bars.copy()
with open(os.path.join(os.path.dirname(__file__), "quotes.txt"), 'r') as f:
    quotes = [x.strip() for x in f.readlines()]
    quote_queue = quotes.copy()

def generate_help_msg(mention: str):
    return f"""{mention} `bar` - return a random wi'erre bar
{mention} `quote` - return a random wi'erre quote
{mention} `add [ quote | bar ]` - add a msg to the database (must be a reply to a message sent by wi'erre)
"""

def write_bars():
    _bars = [x+'\n' for x in bars]
    with open(os.path.join(os.path.dirname(__file__), "bars.txt"), 'w') as f:
        f.writelines(_bars)
    return

def write_quotes():
    _quotes = [x+'\n' for x in quotes]
    with open(os.path.join(os.path.dirname(__file__), "quotes.txt"), 'w') as f:
        f.writelines(_quotes)
    return

@bot.event
async def on_ready():
    activity = discord.Game(f"@me | {__version__}")
    await bot.change_presence(activity=activity)
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message: discord.Message):
    global bars
    global quotes
    global quote_queue
    global bar_queue
    global help_menu
    
    if bot.user.mention in message.content and message.author != bot.user:
        argv = message.content.split(bot.user.mention)[1].strip().split()
        command = argv[0]
        if message.reference is not None and command == 'add':
            if len(argv) == 1:
                await message.channel.send("command `add` missing parameter: `type`")
                await message.channel.send("options: `bar`, `quote`")
                return 

            ref_msg: discord.Message = await message.channel.fetch_message(message.reference.message_id)
            if ref_msg.author.id == 511047686510608384:
                if argv[1] == 'bar':
                    bars.append(ref_msg.content)
                    write_bars()
                elif argv[1] == 'quote':
                    quotes.append(ref_msg.content)
                    write_quotes()
                else:
                    await message.channel.send(f"Unknown type: {argv[1]}")
                    return

                await message.channel.send(f"Added: '{ref_msg.content}'", delete_after=15)
            else:
                await message.channel.send("To add a message, it must have been sent by wi'erre (ID: 511047686510608384).")
        elif command == 'bar':
            # use queue to prevent stale bars from being re-sent before queue has been exhausted
            selection = random.choice(bar_queue)
            bar_queue.remove(selection)
            msg = await message.channel.send(selection)
            await msg.add_reaction(b"\xf0\x9f\x94\xa5".decode()) # fire emoji
            await msg.add_reaction(b"\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\xa6\xaf".decode()) # blind man with cane emoji
            if len(bar_queue) == 0:
                bar_queue = bars.copy()
        elif command == 'quote':
            # use queue to prevent stale quotes from being re-sent before queue has been exhausted
            selection = random.choice(quote_queue)
            quote_queue.remove(selection)
            msg = await message.channel.send(selection)
            await msg.add_reaction(b"\xf0\x9f\x97\xa3\xef\xb8\x8f".decode()) # speaking head silhouette emoji
            await msg.add_reaction(b"\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\xa6\xaf".decode()) # blind man with cane emoji
            if len(quote_queue) == 0:
                quote_queue = quotes.copy()
        elif command == 'queue':
            if len(argv) == 1:
                await message.channel.send("command `queue` missing parameter: `type`")
                await message.channel.send("options: `bar`, `quote`")
                return 
            if message.author.id != 416752352977092611:
                await message.channel.send("You are not authorized to use this command :(")
                return

            if argv[1] == "bar":
                _queue = bar_queue
                if len(argv) == 3:
                    if argv[2] == "reset":
                        bar_queue = bars.copy()
                        await message.channel.send("Successfully reset bar queue")
                        return
            elif argv[1] == "quote":
                _queue = quote_queue
                if len(argv) == 3:
                    if argv[2] == "reset":
                        quote_queue = quotes.copy()
                        await message.channel.send("Successfully reset quote queue")
                        return
            else:
                await message.channel.send(f"unknown queue type: {argv[1]}")
                return
            
            str_queue = ""
            for item in _queue:
                str_queue += '> '+item+'\n\n'
            embed = discord.Embed(
                title=f"Remaining items in queue ({len(_queue)})",
                description=str_queue
            )
            await message.channel.send(embed=embed)
        elif command == '' or command == 'help':
            embed = discord.Embed(
                title="wi'erre bot help",
                description=generate_help_msg(bot.user.mention)
            )
            await message.channel.send(embed=embed)
        else:
            await message.channel.send(f"Unrecognized command: {command}")

bot.run(os.environ["WIERREBOT_TOKEN"])