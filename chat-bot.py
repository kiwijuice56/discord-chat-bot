import os
import discord
from discord.ext import commands
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer

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
CONVO_DIR = os.path.dirname(__file__).join("convos/")

# Phrases to delete in input data
OMITTED_WORDS = {"$teach", "$talk", "$train", "$check"}


# Initialization of discord bot and ai
@bot.event
async def on_ready() -> None:
    global convo_count
    convo_count = len(os.listdir(CONVO_DIR))
    train_ai(basic=False, custom=False, clear=False)
    activity = discord.Game(name="$talk")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print("Logged in as {0.user}".format(bot))


@bot.command()
async def delete(ctx, *args) -> None:
    if not ctx.message.author.guild_permissions.administrator:
        return
    if not args or not args[0].isnumeric():
        await ctx.message.channel.send("**✕ Invalid command!** Must pass in valid (0-based) index for deletion")
    elif int(args[0]) < 0 or int(args[0]) >= len(cache):
        await ctx.message.channel.send("**✕ Invalid command!** Index (0-based) is out of cache bounds")
    else:
        cache.pop(int(args[0]))
        await ctx.message.channel.send("**✓** Cache item deleted")


@bot.command()
async def clear(ctx) -> None:
    if not ctx.message.author.guild_permissions.administrator:
        return
    cache.clear()
    await ctx.message.channel.send("**✓** Cache cleared")


@bot.command()
async def write(ctx) -> None:
    if not ctx.message.author.guild_permissions.administrator:
        return
    write_custom_data(CONVO_DIR)
    await ctx.message.channel.send("**✓** Cache written to file storage")


# Retrains ai after collecting cache
@bot.command()
async def retrain(ctx, *args) -> None:
    valid_args = list(set(args) & set(["basic", "custom", "clear"]))
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
async def info(ctx) -> None:
    embed = discord.Embed(
        title="Help",
        description=
        "Cache ({0}/{1})\\: `{2}`".format(len(cache), CACHE_SIZE, cache) +
        "\nTotal Saved Conversations\\: `{0}`".format(convo_count) +
        "\nCommands:\n"
        "`clear`: (admin) Deletes all of cache\n"
        "`delete {x}`: (admin) Deletes the cache item at index (0-based) x\n"
        "`info`: Sends status of the bot and command information\n"
        "`talk {message}`: Sends the chatbot's response to the message. Alphabetic symbols only\n"
        "`teach {message}`: Stores a conversation based on a reply chain or thread. The root of the thread is the"
        "first message in the conversation while the message parameter is the last message\n"
        "`retrain {basic?} {custom?} {clear?}`: Retrains the chatbot with either the basic English corpus, the custom "
        "corpus from stored conversations, or both. (admin) Using clear as a parameter trains the bot from"
        "a fresh state\n"
        "`write`: (admin) Stores cache to file storage",
        color=0xc7509d
    )
    await ctx.message.channel.send(embed=embed)


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
    if message.reference:
        await get_reply_chain(await message.channel.fetch_message(message.reference.message_id), chain)
    chain.append(message.content)
    return chain


# Processes cached input to prevent errors or oddities in ai training
def process_input(s: str) -> str:
    processed_sentence = []
    for word in s.split():
        if word.startswith(bot.command_prefix):
            continue
        processed_word = "".join([char for char in word.lower() if char.isalpha()])
        if processed_word:
            processed_sentence.append(processed_word)
    processed_input = " ".join(processed_sentence)
    if not processed_input:
        raise EmptyInputException("Input sentence is empty after processing!")
    return processed_input


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
    cache.clear()


# Loads cache from file to list
def load_custom_data(dir_name) -> list:
    convos = []
    for i in range(convo_count):
        f = open(dir_name + "/{0}.txt".format(i), "r", encoding="utf8")
        convos.append([line.strip() for line in f])
        f.close()
    return convos


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
