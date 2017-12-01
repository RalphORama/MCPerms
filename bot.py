import json
import lib.mcapi as mcapi
from lib.pterodactyl import Pterodactyl
from sys import exit
from os.path import isfile
from discord.ext import commands

bot = commands.Bot(command_prefix=commands.when_mentioned)
g_roles = {}
g_panel = None
g_sid = ''


@bot.event
async def on_ready():
    print('Logged in as {}'.format(bot.user))
    print('Loaded {} roles.'.format(len(g_roles.keys())))


@bot.command(pass_context=True)
async def claim(ctx, username):
    channel = ctx.message.channel
    uuid = mcapi.username_to_uuid(username)

    if uuid is None:
        await bot.send_message(channel, 'No UUID found for that username!')
        return

    # TODO: Make sure we don't grant roles to a UUID or Discord user more than
    #       once

    roles_added = []

    for role in ctx.message.author.roles:

        if role.id in g_roles:
            for group in g_roles[role.id]:
                # Debugging
                a = ctx.message.author
                print('Giving {} <{}#{}> group {}'.format(username,
                                                          a.display_name,
                                                          a.discriminator,
                                                          group))

                cmd = 'pex group {} user add {}'.format(group, uuid)

                if g_panel.send_command(g_sid, cmd):
                    roles_added.append(group)

    if not roles_added:
        await bot.send_message(channel, "You're not eligible for any groups.")
    else:
        msg = 'Added {} to {} role(s): **'.format(username, len(roles_added))
        msg = msg + ', '.join(roles_added)
        msg = msg + '**!'
        await bot.send_message(channel, msg)


if __name__ == '__main__':
    files_to_load = ['config.json', 'roles.json']
    for file in files_to_load:
        # Throw an error if our critical config files don't exist
        if not isfile(file):
            exit('{} not found!'.format(file))

    with open('config.json', 'r') as cfg_file:
        cfg = json.load(cfg_file)

    with open('roles.json', 'r') as roles_file:
        g_roles = json.load(roles_file)

    g_panel = Pterodactyl(cfg['pubkey'], cfg['privkey'], cfg['baseURL'])
    g_sid = cfg['serverID']

    # https://discordapp.com/oauth2/authorize?client_id=385950397493280805&scope=bot&permissions=67584
    bot.run(cfg['token'])
