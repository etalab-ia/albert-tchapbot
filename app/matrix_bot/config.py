# SPDX-FileCopyrightText: 2023 Pôle d'Expertise de la Régulation Numérique <contact.peren@finances.gouv.fr>
#
# SPDX-License-Identifier: MIT
import json
import logging
from pathlib import Path

import structlog
from nio.crypto import ENCRYPTION_ENABLED
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotLibConfig(BaseSettings):
    """
    A class to handle built-in user-configurable settings, including support for saving to and loading from a file.
    Can be inherited from by bot developers to implement custom settings.
    """

    timeout: int = Field(
        default=60_000,
        description="The maximum time that the server should wait for new events before "
        "it should return the request anyways, in milliseconds",
    )
    encryption_enabled: bool = Field(default=ENCRYPTION_ENABLED)
    ignore_unverified_devices: bool = Field(default=True, description="True by default in Element")
    store_path: Path = Field(
        default="/data/store/", description="path in which matrix-nio store will be written"
    )
    session_path: Path = Field(
        default="/data/session.txt", description="path of the file to store session identifier"
    )
    users_path: Path = Field(
        default="/data/users.json", description="path of the file to store pending users"
    )
    users: dict = Field(default={}, description="pending users")
    log_level: int = Field(default=logging.INFO, description="log level for the library")
    salt: bytes = Field(
        default=b"\xce,\xa1\xc6lY\x80\xe3X}\x91\xa60m\xa8N",
        description="Salt to store your session credentials. Should not change between two runs",
    )
    conversation_obsolescence: int = Field(
        60 * 60, description="time after which a conversation is considered obsolete, in seconds"
    )

    model_config = SettingsConfigDict(env_file=Path(".matrix_bot_env"))

    def __init__(self):
        super().__init__()
        if not self.users_path.exists():
            with open(self.users_path, "w") as f:
                json.dump({}, f)
            self.users = {}
        else:
            with open(self.users_path, "r") as f:
                self.users: dict = json.load(f)

    def save_users(self):
        with open(self.users_path, "w") as f:
            json.dump(self.users, f, indent=2)


bot_lib_config = BotLibConfig()

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(bot_lib_config.log_level),
)
logger = structlog.get_logger("Matrix bot")
logger.info("starting the bot")
