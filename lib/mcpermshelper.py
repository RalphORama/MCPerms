"""Summary
"""
import csv
import discord
import os
from .pterodactyl import Pterodactyl
from os.path import abspath, join, dirname, exists, isfile
from shutil import copy2


class MCPermsHelper():

    """Helper class for the file I/O the bot does.

    Attributes:
        basedir (str): Working directory for the bot.
        claimfile (str): CSV holding claimed account data.
        fieldnames (list): Headers for the `claimfile` csv.
        panel (Pterodactyl): Pterodactyl API instance.
        roles (dict): Dict for converting Discord role -> PEX groups.
        sid (str): Short UUID for the server we're interacting with.
    """

    def __init__(self, roles: dict, panel: Pterodactyl, sid: str,
                 fieldnames: list, basedir=''):
        """Summary

        Args:
            roles (dict): Dict for converting Discord role -> PEX groups.
            panel (Pterodactyl): Pterodactyl API instance.
            sid (str): Short UUID for the server we're interacting with.
            fieldnames (list): Headers for the `claimfile` csv.
            basedir (str, optional): Working directory for the bot.
        """
        self.roles = roles
        self.panel = panel
        self.sid = sid
        self.fieldnames = fieldnames

        if basedir == '':
            self.basedir = abspath(join(dirname(__file__), '..'))
        else:
            self.basedir = basedir

        self.claimfile = join(self.basedir, 'data', 'claimed.csv')

    def create_data_if_not_exists(self, folder: str, files: list):
        """Create the folder structure and files we need for the bot.

        Args:
            folder (str): The folder to create files within.
            files (list): The files to create.
        """
        fullpath = join(self.basedir, folder)

        if not exists(fullpath):
            os.makedirs(fullpath)

        for file in files:
            path = join(fullpath, file)
            if not exists(path):
                with open(path, 'w+') as f:
                    f.write('')

    def instantiate_csv(self, filename: str, fieldnames: list):
        """Instantiate a CSV with the specified field names.

        Args:
            filename (str): Name of the csv to instantiate.
            fieldnames (list): The fieldnames to set as the header.

        Deleted Parameters:
            filepath (str): The full path of the file to populate.
        """
        filepath = join(self.basedir, 'data', filename)

        if not (isfile(filepath) and
                os.stat(filepath).st_size > 0):
            with open(filepath, 'w+', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()

    def check_claim_eligibility(self,
                                author: discord.User,
                                server: discord.Server,
                                uuid: str) -> str:
        """Loop through `data/claimed.csv` to make sure a user isn't claiming a
        second or duplicate account.

        Args:
            author (discord.User): The user we're checking.
            server (discord.Server): The server the claim originated from.
            uuid (str): The UUID of the Minecraft account.

        Returns:
            str: Message describing any or lack of conflicts.
        """
        with open(self.claimfile, 'r', newline='') as claimed_file:
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

    def add_claimed_account(self,
                            author: discord.User,
                            username: str,
                            uuid: str):
        """Add a claimed accounts to `data/claimed.csv`

        Args:
            author (discord.User): The user whose ID and name we're adding.
            username (str): The username of the Minecraft account.
            uuid (str): The UUID of the Minecraft account.
        """
        with open(self.claimfile, 'a', newline='') as claimed_file:
            writer = csv.DictWriter(claimed_file, fieldnames=self.fieldnames)

            writer.writerow({
                'UUID': uuid,
                'USERNAME': username,
                'DISCORD_ID': author.id,
                'DISCORD_NICK': author.name + '#' + author.discriminator,
                'DISCORD_MENTION': author.mention
            })

    @staticmethod
    def copy_from_example(filename: str, parent_dir: str):
        """Create a copy of an example file for the user to edit.
        I.e. cfg/config-example.json -> cfg/config.json

        Args:
            filename (str): The file to create from a template.
            parent_dir (str): Path to the directory containing the file.
        """
        name = filename[0:filename.index('.')]
        ext = filename[filename.index('.'):]
        source = join(parent_dir, '' + name + '-example' + ext)
        dest = join(parent_dir, '' + filename)

        copy2(source, dest)
