"""MCPerms: A Discord -> Minecraft permission syncing bot.

Attributes:
    bot (discord.ext.commands.bot.Bot): The bot, of course.
    g_fieldnames (list): List of fieldnames for `data/claimed.csv`.
    g_panel (pterodactyl.Pterodactyl): API wrapper class for Pterodactyl panel.
    g_roles (dict): List of Discord role IDs and their associated PEX groups.
    g_sid (str): Short UUID of the Minecraft server hosted by Pterodactyl.
"""
import asyncio
import json
import os
import lib.mcapi as mcapi
from lib.mcpermshelper import MCPermsHelper
from lib.pterodactyl import Pterodactyl
from os.path import join
from sys import exit
from discord.ext import commands

bot = commands.Bot(command_prefix=commands.when_mentioned)
g_helper = None
g_fieldnames = ['UUID', 'USERNAME', 'DISCORD_ID', 'DISCORD_NICK',
                'DISCORD_MENTION']


@bot.event
async def on_ready():
    """Code to execute once the bot has successfully logged in to Discord.
    """
    invite_link = ('https://discordapp.com/oauth2/authorize'
                   '?client_id={}'
                   '&scope=bot&permissions=67584').format(bot.user.id)

    print('Logged in as {}'.format(bot.user))
    print('Loaded {} roles.'.format(len(g_helper.roles.keys())))
    print('Invite me to your server:\n    {}\n'.format(invite_link))


@bot.command(pass_context=True)
async def claim(ctx, username: str):
    """Command to claim minecraft permissions.

    Args:
        ctx (TYPE): Context of the invoking command.
        username (str): The Minecraft username to claim.

    Returns:
        TYPE: Nothing. Not even `None`. Just nothing.
    """
    channel = ctx.message.channel
    a = ctx.message.author
    uuid = mcapi.username_to_uuid(username)

    if uuid is None:
        await bot.send_message(channel, 'No UUID found for that username!')
        return

    # Check account UUID and user's Discord ID to make sure neither
    # has (been) registered.
    eligible = g_helper.check_claim_eligibility(a, ctx.message.server, uuid)

    if 'claimed' in eligible or 'registered' in eligible:
        await bot.send_message(channel, eligible)
        return

    # Loop though each group our user is in and give them the role(s) those
    # groups make them eligble for.
    roles = g_helper.roles
    roles_added = []

    for role in ctx.message.author.roles:

        if role.id in roles:
            for group in roles[role.id]:
                cmd = 'pex group {} user add {}'.format(group, uuid)

                # TODO: Make this failure case more verbose.
                if g_helper.panel.send_command(g_helper.sid, cmd):
                    roles_added.append(group)

    if not roles_added:
        await bot.send_message(channel, "You're not eligible for any groups.")
    else:
        g_helper.add_claimed_account(a, username, uuid)

        msg = 'Added {} to {} role(s): **'.format(username, len(roles_added))
        msg = msg + ', '.join(roles_added)
        msg = msg + '**!'
        await bot.send_message(channel, msg)


if __name__ == '__main__':
    # # Create all the data files we need.
    # data_files = ['claimed.csv']
    # create_data_if_not_exists('data', data_files)
    # for file in data_files:
    #     if file[file.index('.'):] == '.csv':
    #         instantiate_csv('data/' + file, g_fieldnames)

    # Create a template config file and quit with an error if a config file
    # doesn't exist.
    cfg_files = ['config.json', 'roles.json']
    for file in cfg_files:
        fullpath = join(os.getcwd(), 'cfg', file)
        # Throw an error and exit if our critical config files don't exist
        if not os.path.isfile(fullpath):
            MCPermsHelper.copy_from_example(file, join(os.getcwd(), 'cfg'))
            exit('{} not found! I just created it for you. Go fill it out.'
                 .format(file))

    with open('cfg/config.json', 'r') as cfg_file:
        cfg = json.load(cfg_file)

    with open('cfg/roles.json', 'r') as roles_file:
        roles = json.load(roles_file)

    panel = Pterodactyl(cfg['pubkey'], cfg['privkey'], cfg['baseURL'])
    g_helper = MCPermsHelper(roles, panel, cfg['serverID'], g_fieldnames)

    g_helper.create_data_if_not_exists('data', ['claimed.csv'])
    g_helper.instantiate_csv('claimed.csv', g_helper.fieldnames)

    bot.run(cfg['token'])
