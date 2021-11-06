# discord-chat-bot
 Implementation of Chatterbot using Discord API.

## Usage
Due to the necessity of storing files to train the AI, the bot is not hosted publicy. You must download this repository and run the `chat-bot.py` script using your own bot account.

### 1. Create your own discord [bot](https://discord.com/developers/docs/intro)
Set up your bot and copy the token in Discord's developer portal at Application > (your application) > Bot > Token. Paste it into `token.txt`.

### 2. Install dependencies
`chat-bot.py` requires the modules that are imported at the top of the script, namely `chatterbot` and `discord.py`. To install these, open a command prompt and type `pip install chatterbot` and `pip install discord.py` and wait for each to install. If running the script gives an error that either of the modules is not found, you may want to use `pip3` instead to ensure the modules are installed to the correct python version. If `chatterbot` fails to install, type `pip install chatterbot=1.0.0` instead.

### 3. Set up `convos` directory
Chatbot saves conversation cached in commands to numbered .txt files. Each file represents one conversation in which each line is a valid response to the one before it. You can create your own files manually (following the number file name scheme) or teach the bot with commands within Discord. You can change this directory by changing the `CONVO_DIR` variable within the `chat-bot.py` script.

### 4. Run the `chat-bot.py` script
Using any python interpreter, run the `chat-bot.py` script. When this script is running, your bot should be online and available for use!

## Commands
####  `$talk args: any`
####  `$teach` (in reply to another message or reply chain)
####  `$train args: 'basic', 'custom', 'clear'`
####  `$cache_handle args: 'clear', 'write'`
####  `$check`
