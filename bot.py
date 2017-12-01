"""Summary

Attributes:
    bot (TYPE): Description
    g_fieldnames (TYPE): Description
    g_panel (TYPE): Description
    g_roles (dict): Description
    g_sid (str): Description
"""
import csv
import discord
import json
import os
import lib.mcapi as mcapi
from lib.pterodactyl import Pterodactyl
from shutil import copy2
from sys import exit
from discord.ext import commands

bot = commands.Bot(command_prefix=commands.when_mentioned)
g_roles = {}
g_panel = None
g_sid = ''
g_fieldnames = ['UUID', 'USERNAME', 'DISCORD_ID', 'DISCORD_NICK',
                'DISCORD_MENTION']


def create_data_if_not_exists(folder: str, files: list):
    """Create the folder structure and files we need for the bot.

    Args:
        folder (str): The folder to create files within.
        files (list): The files to create.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)

    for file in files:
        path = '{}/{}'.format(folder, file)
        if not os.path.exists(path):
            with open(path, 'w+') as f:
                f.write('')


def copy_from_example(filename: str):
    """Create a copy of an example file for the user to edit.
    I.e. cfg/config-example.json -> cfg/config.json

    Args:
        filename (str): The file to create from a template.
    """
    name = filename[0:filename.index('.')]
    ext = filename[filename.index('.'):]
    source = '' + name + '-example' + ext
    dest = '' + filename

    copy2(source, dest)


def instantiate_csv(filepath: str, fieldnames: list):
    """Instantiate a CSV with the specified field names.

    Args:
        filepath (str): The full path of the file to populate.
        fieldnames (list): The fieldnames to set as the header.
    """

    if not (os.path.isfile(filepath) and
            os.stat(filepath).st_size > 0):
        with open(filepath, 'w+', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()


def check_claim_eligibility(author: discord.User, server: discord.Server, uuid: str) -> str:
    """Loop through `data/claimed.csv` to make sure a user isn't claiming a
    second or duplicate account.

    Args:
        author (discord.User): The user we're checking.
        server (discord.Server): The server the claim originated from.
        uuid (str): The UUID of the Minecraft account.

    Returns:
        str: Message describing any or lack of conflicts.
    """
    with open('data/claimed.csv', 'r', newline='') as claimed_file:
        reader = csv.DictReader(claimed_file)

        for row in reader:
            # Respond whether we get a UUID match, Discord ID match,
            # or no match

            if (row['DISCORD_ID'] == author.id):
                msg = 'You already registered account {} [`{}`].'
                return msg.format(row['USERNAME'], row['UUID'])
            elif (row['UUID'] == uuid):
                if server.get_member(row['DISCORD_ID']):
                    tag = row['DISCORD_MENTION']
                else:
                    tag = row['DISCORD_NICK']

                msg = '{} already claimed account {} [`{}`].'
                return msg.format(tag, row['USERNAME'], row['UUID'])

        # The for loop doesn't execute if there are no rows in the file.
        # Thus, this part is outside to catch both 'not found' and
        # 'fresh file' cases.
        msg = 'OK for you to register this nick with this account.'
        return msg


def add_claimed_account(author: discord.User, username: str, uuid: str):
    """Add a claimed accounts to `data/claimed.csv`

    Args:
        author (discord.User): The user whose ID and name we're adding.
        username (str): The username of the Minecraft account.
        uuid (str): The UUID of the Minecraft account.
    """
    with open('data/claimed.csv', 'a', newline='') as claimed_file:
        writer = csv.DictWriter(claimed_file, fieldnames=g_fieldnames)

        writer.writerow({
            'UUID': uuid,
            'USERNAME': username,
            'DISCORD_ID': author.id,
            'DISCORD_NICK': author.name + author.discriminator,
            'DISCORD_MENTION': author.mention
        })


@bot.event
async def on_ready():
    """Summary
    """
    print('Logged in as {}'.format(bot.user))
    print('Loaded {} roles.'.format(len(g_roles.keys())))


@bot.command(pass_context=True)
async def claim(ctx, username):
    """Summary

    Args:
        ctx (TYPE): Description
        username (TYPE): Description

    Returns:
        TYPE: Description
    """
    channel = ctx.message.channel
    a = ctx.message.author
    uuid = mcapi.username_to_uuid(username)

    if uuid is None:
        await bot.send_message(channel, 'No UUID found for that username!')
        return

    # Check account UUID and user's Discord ID to make sure neither
    # has (been) registered.
    eligible = check_claim_eligibility(a, ctx.message.server, uuid)

    if 'claimed' in eligible or 'registered' in eligible:
        await bot.send_message(channel, eligible)
        return

    # Loop though each group our user is in and give them the role(s) those
    # groups make them eligble for.
    roles_added = []

    for role in ctx.message.author.roles:

        if role.id in g_roles:
            for group in g_roles[role.id]:
                cmd = 'pex group {} user add {}'.format(group, uuid)

                # TODO: Make this failure case more verbose.
                if g_panel.send_command(g_sid, cmd):
                    roles_added.append(group)

    if not roles_added:
        await bot.send_message(channel, "You're not eligible for any groups.")
    else:
        add_claimed_account(a, username, uuid)

        msg = 'Added {} to {} role(s): **'.format(username, len(roles_added))
        msg = msg + ', '.join(roles_added)
        msg = msg + '**!'
        await bot.send_message(channel, msg)


if __name__ == '__main__':
    data_files = ['claimed.csv']
    create_data_if_not_exists('data', data_files)
    for file in data_files:
        if file[file.index('.'):] == '.csv':
            instantiate_csv('data/' + file, g_fieldnames)

    cfg_files = ['cfg/config.json', 'cfg/roles.json']
    for file in cfg_files:
        # Throw an error and exit if our critical config files don't exist
        if not os.path.isfile(file):
            copy_from_example(file)
            exit('{} not found! I just created it for you. Go fill it out.'
                 .format(file))

    with open('cfg/config.json', 'r') as cfg_file:
        cfg = json.load(cfg_file)

    with open('cfg/roles.json', 'r') as roles_file:
        g_roles = json.load(roles_file)

    g_panel = Pterodactyl(cfg['pubkey'], cfg['privkey'], cfg['baseURL'])
    g_sid = cfg['serverID']

    # https://discordapp.com/oauth2/authorize?client_id=385950397493280805&scope=bot&permissions=67584
    bot.run(cfg['token'])
