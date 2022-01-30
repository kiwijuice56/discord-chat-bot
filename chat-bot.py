import os
import discord
from discord.ext import commands
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
from chatterbot.trainers import ListTrainer

# Get secret discord bot token
TOKEN = open("token.txt", "r").readline()

# Initialize discord bot
bot = commands.Bot(command_prefix='$')
ai = None

# Temporary storage of training input, written to files in CONVO_DIR once cache is full to CACHE_SIZE
cache = []
CACHE_SIZE = 32

# Conversation files
convo_count = 0
CONVO_DIR = "convos/"

# Phrases to delete in input data
OMITTED_WORDS = {"$teach", "$talk", "$train", "$check"}


# Initialization of discord bot and ai
@bot.event
async def on_ready() -> None:
    global convo_count
    convo_count = len(os.listdir(CONVO_DIR))
    train_ai(basic=False, custom=False, clear=False)
    await update_status("$talk")
    print("Logged in as {0.user}".format(bot))


# Allows admins to handle cache by deleting items, writing them to a file, or clearing it entirely
@bot.command()
async def edit(ctx, *args) -> None:
    valid_args = [arg for arg in args if arg in ["clear", "write", "delete"]]
    num_args = [int(arg) for arg in args if arg.isnumeric()]
    is_admin = ctx.message.author.guild_permissions.administrator
    if len(valid_args) == 0 or len(valid_args) > 1:
        await ctx.message.channel.send("**✕ Invalid command!** Use only one valid argument: "
                                       "`clear`, `write`, `delete i`")
    elif not is_admin:
        await ctx.message.channel.send("**✕ Invalid command!** Must be admin to handle cache")
    else:
        write, clear, delete = "write" in valid_args, "clear" in valid_args, "delete" in valid_args
        if write:
            write_custom_data(CONVO_DIR)
        if clear:
            clear_cache()
        if delete:
            num = -1
            for arg in num_args:
                num = arg
                break
            try:
                delete_cache_item(num)
            except IndexError:
                await ctx.message.channel.send("**✕ Invalid command!** Must pass in valid index for deletion")
                return
        await ctx.message.channel.send("**✓ Cache handled!** {0} ".format(valid_args))
        
        
# Retrains ai after collecting cache
@bot.command()
async def train(ctx, *args) -> None:
    valid_args = [arg for arg in args if arg in ["basic", "custom", "clear"]]
    is_admin = ctx.message.author.guild_permissions.administrator
    if len(valid_args) == 0:
        await ctx.message.channel.send("**✕ Invalid command!** Use at least one valid argument: "
                                       "`basic`, `custom`, `clear`")
    else:
        basic, custom, clear = "basic" in valid_args, "custom" in valid_args, "clear" in valid_args
        is_admin = ctx.message.author.guild_permissions.administrator
        if clear and not is_admin:
            await ctx.message.channel.send("**✕ Invalid argument!** Must be admin to clear AI storage: "
                                           "continuing without clear")
        train_ai(basic, custom, clear and is_admin)
        await ctx.message.channel.send("**✓ AI retrained!** {0}".format(valid_args))


# Messages channel with status of bot
@bot.command()
async def check(ctx) -> None:
    await ctx.message.channel.send("\n".join([
        "**Chatbot check\\:**",
        "Cache ({0}/{1})\\: `{2}`".format(len(cache), CACHE_SIZE, cache),
        "Saved conversations\\: `{0}`".format(convo_count)
    ]))


# Retrieves phrase from ai according to message input
@bot.command()
async def talk(ctx, *args) -> None:
    try:
        sentence = process_input(" ".join(args))
        await ctx.message.channel.send(process_input(str(ai.get_response(sentence))))
    except EmptyInputException:
        await ctx.message.channel.send("**✕ Invalid input!** Empty message (after stripping symbols, numbers, "
                                       "and commands)")


# Accepts a pair of messages (with the invoking message being a reply) to add to cache
@bot.command()
async def teach(ctx) -> None:
    try:
        chain = await get_reply_chain(ctx.message)
        cache_custom_data(chain)
        await ctx.message.channel.send("**✓ Conversation cached!**")
    except NotAConversationException:
        await ctx.message.channel.send("**✕ Invalid input!** Ensure you are replying to another message, as the "
                                       "reply chain is interpreted as a conversation to train the AI")
    except EmptyInputException:
        await ctx.message.channel.send("**✕ Invalid input!** One or more messages are empty after processing: "
                                       "ensure all messages consist of some lowercase letters")


# Retrieves every message in a reply chain
async def get_reply_chain(message, chain=None) -> list:
    if chain is None:
        chain = []
    if message.reference is None:
        return [message.content] + chain
    return await get_reply_chain(await message.channel.fetch_message(message.reference.message_id), [message.content] + chain)


# Processes cached input to prevent errors or oddities in ai training
def process_input(s: str) -> str:
    sentence = s.split()
    processed_sentence = []
    for word in sentence:
        if word in OMITTED_WORDS:
            continue
        basic_word = "".join([c for c in word.lower() if c.isalpha()])
        if len(basic_word) > 0:
            processed_sentence.append(basic_word)
    processed_word = " ".join(processed_sentence)
    if processed_word.isspace() or len(processed_word) == 0:
        raise EmptyInputException("Input sentence is empty after processing!")
    return processed_word


# Boilerplate code to allow for logging/clear prevention
def clear_cache() -> None:
    global cache
    cache.clear()


# Delete item at specific index of cache, ensuring that negative indices are also handled as an error
def delete_cache_item(index: int) -> None:
    global cache
    if index < 0:
        raise IndexError
    cache.pop(index)


# Add interaction to cache list 
def cache_custom_data(convo: list) -> None:
    global cache
    if len(cache) >= CACHE_SIZE:
        write_custom_data(CONVO_DIR)
    processed_convo = [process_input(sentence) for sentence in convo]
    if len(processed_convo) < 2:
        raise NotAConversationException("Reply chain is less than two messages")
    cache.append(processed_convo)


# Writes cache to file for storage
def write_custom_data(dir_name) -> None:
    global cache
    global convo_count
    for convo in cache:
        f = open(dir_name + "{0}.txt".format(convo_count), "a", encoding="utf8")
        for line in convo:
            f.write(line + "\n")
        f.close()
        convo_count += 1
    clear_cache()


# Loads cache from file to list
def load_custom_data(dir_name) -> list:
    convos = []
    for i in range(convo_count):
        f = open(dir_name + "/{0}.txt".format(i), "r", encoding="utf8")
        convos.append([line.strip() for line in f])
        f.close()
    return convos


# Sets discord play status
async def update_status(status: str) -> None:
    activity = discord.Game(name=status)
    await bot.change_presence(status=discord.Status.online, activity=activity)


# Trains ai from basic english corpus and custom list data
def train_ai(basic: bool, custom: bool, clear: bool) -> None:
    global ai
    ai = ChatBot("chat-bot")
    if clear:
        ai.storage.drop()
    if custom:
        custom_trainer = ListTrainer(ai)
        write_custom_data(CONVO_DIR)
        for convo in load_custom_data(CONVO_DIR):
            custom_trainer.train(convo)
    if basic:
        basic_trainer = ChatterBotCorpusTrainer(ai)
        basic_trainer.train("chatterbot.corpus.english")
    

# Exception for a convo with less than 2 messages
class NotAConversationException(Exception):
    pass


# Exception for a convo containing an empty input
class EmptyInputException(Exception):
    pass


# Exception for a command with invalid arguments
class InvalidArgumentsException(Exception):
    pass


bot.run(TOKEN)
