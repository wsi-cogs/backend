import base64
from hashlib import md5

from aiohttp.web import Application
from blowfish import Cipher


class BlowfishDecryption:
    def __init__(self, passphrase: bytes):

        key = md5(passphrase).digest()
        while len(key) < 56:
            key += md5(key).digest()
        key = key[:56]

        self.cipher = Cipher(key)

    def decrypt(self, data: str):
        blob = base64.b64decode(data + "==", "-_")
        iv, data = blob[:8], blob[8:]
        plaintext = b"".join(self.cipher.decrypt_cbc(data, iv))
        no_to_remove = plaintext[-1]
        plaintext = plaintext[8:-no_to_remove]
        return plaintext


def init_blowfish(app: Application) -> None:
    app.blowfish = BlowfishDecryption(app["config"]["login_db"]["blowfish_key"].encode())
