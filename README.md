# discord-chat-bot
Implementation of [Chatterbot](https://github.com/gunthercox/ChatterBot) using Discord API. This project uses some functionality of Chatterbot, but is not endorsed by Chatterbot nor a distribution of the code.

## Usage
Due to the necessity of storing files to train the AI, the bot is not hosted publicy. You must download this repository and run the `chat-bot.py` script using your own bot account.

### 1. Create your own discord [bot](https://discord.com/developers/docs/intro)
Set up your bot and copy the token in Discord's developer portal at Application > (your application) > Bot > Token. Paste it into `token.txt`.

### 2. Install dependencies
`chat-bot.py` requires the modules that are imported at the top of the script, namely `chatterbot` and `discord.py`. To install these, open a command prompt and type `pip install chatterbot` and `pip install discord.py` and wait for each to install. If running the `chat-bot.py` script gives an error that either of the modules are not found, you should attempt to use `pip3` instead to ensure the modules are installed to the correct python version. If `chatterbot` fails to install, type `pip install chatterbot=1.0.0` instead.

### 3. Set up `convos` directory
Chatbot saves conversations cached by discord users to numbered `.txt` files. Each file represents one conversation in which each line is a valid response to the one before it. You can create your own files manually (following the number file name scheme) or teach the bot with commands within Discord (see below). You can change the directory in which conversations are saved by changing the `CONVO_DIR` variable within the `chat-bot.py` script.

### 4. Run the `chat-bot.py` script
Using any python interpreter, run the `chat-bot.py` script. When this script is running, your bot should be online and available for use!

## Commands
* #### `$talk args: any`
Takes any string of lowercase letters as input for the AI to respond to. Any bot commands, numbers, and symbols are stripped before being interpreted.
* #### `$teach` (in reply to another message or reply chain)
Takes every message in a reply chain and caches it as a conversation. If cache is full, all conversations will be saved.
* #### `$train args: 'basic', 'custom', 'clear'`
Retrains AI. All the cache is saved before training. `basic` will train based on the default English corpus, `custom` will train based on saved conversations, and `clear` will reset the AI storage (not saved custom conversations) before retraining. `clear` is accessible only to administrators of the server. Note that while one parameter is required, more than one can be passed in at once.
* #### `$cache_handle args: 'clear', 'write'`
Modifies cache. `clear` will reset the cache and delete recently taught conversations. `write` will save all conversations in the cache. Accessible only to administrators of the server.
* #### `$check`
Sends status.
