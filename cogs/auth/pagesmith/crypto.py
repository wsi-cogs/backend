"""
Copyright (c) 2017 Genome Research Ltd.

Authors:
* Simon Beal <sb48@sanger.ac.uk>
* Christopher Harrison <ch12@sanger.ac.uk>
* Joshua Randall <jr17@sanger.ac.uk>

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

from hashlib import md5

from blowfish import Cipher


class BlowfishCBCDecrypt:
    """ Blowfish decryption in CBC mode with Perl compatibility """
    def __init__(self, passphrase:bytes) -> None:
        """
        Constructor: Initialise the cipher with the key derived from the
        passphrase in the same way Perl does it

        :param passphrase:
        :return:
        """
        key = md5(passphrase).digest()
        while len(key) < 56:
            key += md5(key).digest()
        key = key[:56]

        self.cipher = Cipher(key)

    def decrypt(self, ciphertext:bytes) -> bytes:
        """
        Decrypt the ciphertext

        :param ciphertext:
        :return:
        """
        iv, data = ciphertext[:8], ciphertext[8:]
        padded_plaintext = b"".join(self.cipher.decrypt_cbc(data, iv))
        padding = int(padded_plaintext[-1])
        return padded_plaintext[8:-padding]
