# MCPerms

A lightweight link between Discord, Pterodactyl Panel, and Minecraft.

# About

I designed MCPerms because there were no decent Spigot plugins that allowed me to grant users on my Minecraft server permissions based on their roles in a Discord server. I wanted a system that would check Discord roles for a user and add them to one or more groups in PermissionsEx, the permissions management plugin I use.

# Installation

This bot is designed for self-hosted instances, as configuration requires knowledge of Pterodactyl Panel private API keys and server UUIDs.

The bot is written entirely in Python, as I'm not familiar with Java and the Spigot API. Because of that, it does not run as a plugin on a Spigot server. Instead, it runs in its own process and interacts with the server via the [Pterodactyl API](https://docs.pterodactyl.io/v0.6/reference).

Due to this limitation, you cannot use this bot with a 'raw' Spigot installation. Instead, you need to install and use [Pterodactyl Panel](https://pterodactyl.io/) to manage your Spigot server.

Once you've got Pterodactyl and your Spigot server set up, installation is simple:

1. Navigate to the "API Access" page within the panel and generate a keypair like so: ![API key options](https://i.imgur.com/bmSJIVq.png)
2. Copy the public key and the secret: ![API key and secret](https://i.imgur.com/eDA84kY.png)
3. In the `cfg` folder, copy `config-example.json` to `config.json` and input:
    - Your Discord Bot Token.
    - The public/private keypair for Pterodactyl.
    - The base URL of your panel API.
    - The short UUID of your Spigot server.
4. Also in the `cfg` folder, copy `roles-example.json` to `roles.json` and specify which Discord roles equate to which PermissionsEx groups.
    - NB: One Discord role can equate to multiple PEX groups, but not the other way around.
    - `{"<DISCORD_ROLE_ID": ["PEX_GROUP_1", "PEX_GROUP_2", "ETC."]}`
5. In the bot's root folder, run `pip install -r requirements.txt`.
6. Run the bot via `python bot.py` (`pyton3 bot.py` on some systems).
7. Visit the invite link, add the bot to your server, and get cracking!

# Usage

As of the time of writing, the bot only has two commands, both using a mention of the bot as the command prefix:

- `claim <Minecraft username>`: Grants the Minecraft account permissions on the server (if the Discord user is eligible).
- `listroles`: Lists all of the server's roles and their IDs (for `roles.json`)
