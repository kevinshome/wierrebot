import os
import sys
import sqlite3
import random
import discord
import traceback
from discord.ext.commands.bot import Bot
from dotenv import load_dotenv
from . import __version__

try:
    DATABASE_LOC = sys.argv[1]
    DATABASE = sqlite3.connect(DATABASE_LOC)
    _dbcursor = DATABASE.cursor()
    for i in ["bar", "quote"]:
        _dbcursor.execute(
            f"CREATE TABLE IF NOT EXISTS \"{i}\"(content TEXT NOT NULL UNIQUE)"
        )
    _dbcursor.close()
    del _dbcursor
except IndexError:
    sys.stderr.write("requires path to database as first argument (no_exist=ok)...\n")
    raise SystemExit(1)

class wbList(list):
    def __init__(self, ltype, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = ltype
        self._refill()
    def append(self, obj, /):
        """Append item to wbList, and add it to database."""

        # if message is unique, add to queue and database
        _cursor = DATABASE.cursor()
        _cursor.execute(f"INSERT INTO \"{self.type}\" VALUES(?)", (obj.strip(),))
        super().append(obj)
        DATABASE.commit()
        _cursor.close()
    def pop(self):
        """Remove last item of wbList, and if empty, refill."""
        _popped = super().pop()
        if len(self) == 0:
            self._refill()
        return _popped
    def _refill(self):
        """Method used by lists to refill themselves when exhausted."""
        _cursor = DATABASE.cursor()
        if len(self) != 0:
            raise Exception("Unable to refill partially filled list. Create a new wbList object instead.")
        response = _cursor.execute(
            f"SELECT * FROM \"{self.type}\""
        ).fetchall()
        _cursor.close()
        for item in response:
            super().append(item[0])
        random.shuffle(self)

class WierreBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.responses = {
            "bar": {
                "queue": wbList("bar"), 
                "reactions": {
                    "positive": b"\xf0\x9f\x94\xa5".decode(), 
                    "negative": b"\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\xa6\xaf".decode()
                    }
                },
            "quote": {
                "queue": wbList("quote"), 
                "reactions": {
                    "positive": b"\xf0\x9f\x97\xa3\xef\xb8\x8f".decode(), 
                    "negative": b"\xf0\x9f\x91\xa8\xe2\x80\x8d\xf0\x9f\xa6\xaf".decode()
                }
            }
        }
    async def on_command_error(self, ctx, exception):
        await ctx.chanel.send(
            "The following error occurred during command handling:\n"
            f"`{traceback.print_exception(exception)}`"
        )


load_dotenv()
intents = discord.Intents.default()
bot = WierreBot(intents=intents)

def generate_help_msg(mention: str):
    return f"""{mention} `bar` - return a random wi'erre bar
{mention} `quote` - return a random wi'erre quote
{mention} `add [ quote | bar ]` - add a msg to the database (must be a reply to a message sent by wi'erre)
"""

@bot.event
async def on_ready():
    activity = discord.Game(f"@me | {__version__}")
    await bot.change_presence(activity=activity)
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message: discord.Message):

    if bot.user.mention in message.content and message.author != bot.user:
        argv = message.content.split(bot.user.mention)[1].strip().split()
        command = argv[0]
        if message.reference is not None and command == 'add':
            if len(argv) == 1:
                await message.channel.send(
                    "command `add` missing parameter: `type`\n"
                    "options: `bar`, `quote`"
                )
                return 


            ref_msg: discord.Message = message.reference.cached_message or await message.channel.fetch_message(message.reference.message_id)
            if ref_msg.author.id != 511047686510608384:
                await message.channel.send("To add a message, it must have been sent by wi'erre.")
                return

            try:
                bot.responses[argv[1]]["queue"].append(ref_msg.content)
                await message.channel.send(f"Added: '{ref_msg.content}'", delete_after=15)
            except KeyError:
                await message.channel.send(f"Unknown type: {argv[1]}")
            except sqlite3.IntegrityError:
                await message.channel.send(f"That {argv[1]} already exists in the database!")

        elif message.reference is None and command == 'add':
            await message.channel.send("The 'add' command must be used in a reply to the message you would like to add.")
        elif command in ["bar", "quote"]:
            selection = bot.responses[command]["queue"].pop()
            msg = await message.channel.send(selection)
            await msg.add_reaction(bot.responses[command]["reactions"]["positive"])
            await msg.add_reaction(bot.responses[command]["reactions"]["negative"])
        elif command == 'queue':
            if len(argv) == 1:
                await message.channel.send("command `queue` missing parameter: `type`")
                await message.channel.send("options: `bar`, `quote`")
                return 
            if message.author.id != 416752352977092611:
                await message.channel.send("You are not authorized to use this command :(")
                return

            _rtype = argv[1]
            try:
                if len(argv) == 3 and argv[2] == "reset":
                    bot.responses[_rtype]["queue"] = wbList(_rtype)
                    await message.channel.send(f"Successfully reset {_rtype} queue")
                    return
            except KeyError:
                await message.channel.send(f"unknown queue type: {_rtype}")
                return

            _queue = bot.responses[_rtype]["queue"]
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
