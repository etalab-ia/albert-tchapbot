# SPDX-FileCopyrightText: 2021 - 2022 Isaac Beverly <https://github.com/imbev>
# SPDX-FileCopyrightText: 2023 Pôle d'Expertise de la Régulation Numérique <contact.peren@finances.gouv.fr>
#
# SPDX-License-Identifier: MIT

import base64
import json
import secrets
from dataclasses import dataclass
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from matrix_bot.config import bot_lib_config, logger


def _get_key_from_password(password: str, salt):
    """calculate a cryptographic key from the password"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend(),
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode(encoding="utf-8")))


def encrypt(data: str, password: str, salt=bot_lib_config.salt) -> str:
    """encrypt the data given with the password"""
    fernet_encoder = Fernet(_get_key_from_password(password, salt))
    return fernet_encoder.encrypt(data.encode(encoding="utf-8")).decode()


def decrypt(encrypted_data: str, password: str, salt=bot_lib_config.salt) -> str:
    """decrypt the data given with the password"""
    fernet_encoder = Fernet(_get_key_from_password(password, salt))
    return fernet_encoder.decrypt(encrypted_data.encode(encoding="utf-8")).decode()


@dataclass(frozen=True)
class Credentials:
    """
    A class to store and handle login credentials.
    """

    homeserver: str
    """The homeserver for the bot to connect to. Begins with "https://"."""
    username: str
    """The username of the bot to connect to"""
    password: str
    """The password of the bot to connect to"""
    session_stored_file: Path = bot_lib_config.session_path
    """Path to the file that will be used to store the session informations"""


@dataclass
class AuthLogin:
    """
    A class to store and handle login credentials.
    Store the session information in a file encrypted with the password
    """

    credentials: Credentials
    device_id: str = ""
    access_token: str = ""
    device_name: str = ""

    def __post_init__(self):
        self.session_stored_file_path = (
            Path(self.credentials.session_stored_file)
            if self.credentials.session_stored_file
            else None
        )
        self.device_name = f"Bot Client using Matrix-Bot id {secrets.token_urlsafe(20)}"
        self.read_session_file()

    def read_session_file(self):
        """Reads and decrypts the device_id and access_token from file"""
        if not self.session_stored_file_path or not self.session_stored_file_path.exists():
            return
        with open(self.session_stored_file_path, "r") as store_file:
            encrypted_session_data = store_file.read()
        try:
            self.device_id, self.access_token, self.device_name = json.loads(
                decrypt(encrypted_session_data, self.credentials.password)
            )
        except InvalidToken as invalid_token:
            raise ValueError(
                f"session saved is not loaded. The file {self.session_stored_file_path.resolve()} "
                f"is not compatible with this version of botlib and should be removed"
            ) from invalid_token

    def write_session_file(self):
        """Encrypts and writes to file the device_id and access_token."""
        if not self.session_stored_file_path:
            logger.info("device_id and access_token will not be saved")
            return

        if not (self.device_id and self.access_token):
            raise ValueError(f"Can't save credentials: {self.device_id=} or {self.access_token=}")
        encrypted_session = encrypt(
            json.dumps([self.device_id, self.access_token, self.device_name]),
            self.credentials.password,
        )
        with open(self.session_stored_file_path, "w") as store_file:
            store_file.write(encrypted_session)
