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
        return plaintext.rstrip(b"\x04")


def init_blowfish(app: Application) -> None:
    app.blowfish = BlowfishDecryption(app["login_db"]["blowfish_key"].encode())

if __name__ == "__main__":
    import os
    from config import load_config
    conf = load_config(os.path.join("config", "config.yaml"))
    blowfish = BlowfishDecryption(conf["login_db"]["blowfish_key"].encode())
    encrypted = 'UmFuZG9tSVbaF2GYLbV-9OXiXVSaoU33cHe-nfzWU1OyHDBnTs-9hR67yITes49d6MY6r8JiOXHxMO0Jl2dShEzHIpnaDvS5'
    print(blowfish.decrypt(encrypted))
