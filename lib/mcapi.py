from requests import get
from json import loads
from time import time
from uuid import UUID


def username_to_uuid(username, when=int(time())):
    url = 'https://api.mojang.com/users/profiles/minecraft/{}?at={}'

    r = get(url.format(username, when))

    if r.status_code == 200:
        data = loads(r.text)
        uuid = UUID(data['id'])
        return str(uuid)

    return None
