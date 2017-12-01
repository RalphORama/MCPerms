"""Summary
"""
import hmac
import json
import requests
from base64 import b64encode
from hashlib import sha256


class Pterodactyl():

    """Summary

    Attributes:
        api (str): Base URL for the Pterodactyl API
        privkey (str): API private key
        pubkey (str): API public key
        timeout (int): Timeout for API requests
    """

    def __init__(self, pubkey: str, privkey: str, api: str, timeout=500):
        """A wrapper for the Pterodactyl Panel API

        Args:
            pubkey (str): Public part of the generated keypair
            privkey (str): Private part of the generated keypair
            api (str): Base URL for the panel's API
            timeout (int, optional): How long to wait before requests time out.
        """
        self.pubkey = pubkey
        # This is only ever used as an encoded value, so we encode it here.
        self.privkey = privkey.encode('utf8')
        self.api = api
        self.timeout = timeout

    def generate_hmac(self, url: str, body='') -> str:
        """
        The authorization header for API requests is simply a combination of a
        few different things and is sent in the format
        <public_key>.<sha256 hmac of url and body>.

        Args:
            url (str): The path appended to the API URL we're targeting
            body (str, optional): Data we're sending to the server

        Returns:
            str: The authentication token for the request
        """
        # Append the endpoint to the API URL
        target = self.api + url
        # Encode the message for hashing
        msg = (target + body).encode('utf-8')
        # Hash and encode the message
        h = hmac.new(self.privkey, msg, sha256)
        encoded = b64encode(h.digest())

        # Return the required auth token
        # encoded.decode() is simply bytes to string, not decoded base64
        return self.pubkey + '.' + encoded.decode('utf-8')

    def list_user_servers(self) -> dict:
        """
        Lists all the servers the user has access to, including as a subuser.
        Does NOT list all the servers on the system.

        Returns:
            dict: A dict of every accessible server.
        """
        url = '/user'
        auth = {'Authorization': 'Bearer {}'.format(self.generate_hmac(url))}

        r = requests.get(self.api + url, headers=auth, timeout=self.timeout)

        return json.loads(r.text)

    def send_command(self, sid: str, command: str) -> bool:
        """Executes a command on the specified server.

        Args:
            sid (str): Short UUID of the server, e.g. `a8f39zb7`.
            command (str): The command to execute.

        Returns:
            bool: True if the command executed, false otherwise.
        """
        url = '/user/server/{}/command'.format(sid)
        data = json.dumps({"command": command})

        token = self.generate_hmac(url, data)
        headers = {'Authorization': 'Bearer {}'.format(token),
                   'content-type': 'application/json'}

        r = requests.post(self.api + url, headers=headers,
                          data=data,
                          timeout=self.timeout)

        # Debugging
        print(r.text)

        if r.status_code == 204:
            return True

        return False
