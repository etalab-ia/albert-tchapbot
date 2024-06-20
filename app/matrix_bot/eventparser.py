# SPDX-FileCopyrightText: 2021 - 2022 Isaac Beverly <https://github.com/imbev>
# SPDX-FileCopyrightText: 2023 Pôle d'Expertise de la Régulation Numérique <contact.peren@finances.gouv.fr>
# SPDX-FileCopyrightText: 2024 Etalab <etalab@modernisation.gouv.fr>
#
# SPDX-License-Identifier: MIT
import re
from dataclasses import dataclass

from config import env_config
from nio import Event, MatrixRoom, RoomMessageText

from .client import MatrixClient
from .config import bot_lib_config, logger
from .room_utils import room_is_direct_message


class EventNotConcerned(Exception):
    """Exception to say that the current event is not concerned by this parser"""


@dataclass
class EventParser:
    """
    Parse the current event for the callbacks.
    Many useful methods that raises a EventNotConcerned when the action do not concern the current event
    """

    room: MatrixRoom
    event: Event
    matrix_client: MatrixClient
    log_usage: bool = False

    @property
    def sender(self) -> str:
        return self.event.sender

    def is_from_userid(self, userid: str) -> bool:
        return self.sender_id() == userid

    def is_from_this_bot(self) -> bool:
        return self.is_from_userid(self.matrix_client.user_id)

    def is_sender_domain_allowed(self) -> bool:
        if "*" in env_config.user_allowed_domains:
            return True
        return self.sender_domain() in env_config.user_allowed_domains

    def room_is_direct_message(self) -> bool:
        return room_is_direct_message(self.room)

    def sender_id(self) -> str:
        return self.event.sender

    def sender_username(self) -> str:
        return self.room.users[self.event.sender].name

    def sender_domain(self) -> str | None:
        """
        Sender IDs are formatted like this: "@<mail_username>-<mail_domain>:<matrix_server>
        e.g. @john.doe-ministere_example.gouv.fr1:agent.ministere_example.tchap.gouv.frmerci
        """
        match: re.Match[str] | None = re.search(
            r"(?<=\-)[^\-\:]+[0-9]*(?=\:)", self.event.sender
        )  # match the domain name (between the last "-" and ":", with optional numbers to ignore at the end of the domain) WARNING: this regex is not perfect and doesn't work for domain names with dashes in it like "developpement-durable.gouv.fr"
        if match:
            return match.group(0)
        logger.warning("Could not extract domain from sender ID", sender_id=self.sender_id)

    def do_not_accept_own_message(self) -> None:
        """
        :raise EventNotConcerned: if the message is written by the bot.
        """
        if self.is_from_this_bot():
            raise EventNotConcerned

    def only_on_direct_message(self) -> None:
        """
        :raise EventNotConcerned: if the room is a not a direct message room.
        """
        if not self.room_is_direct_message():
            raise EventNotConcerned

    def only_on_salons(self) -> None:
        """
        :raise EventNotConcerned: if the room is a direct message room.
        """
        if self.room_is_direct_message():
            raise EventNotConcerned

    def only_on_join(self) -> None:
        """
        :raise EventNotConcerned: if the event is not a join event (the bot has been invited)
        """
        if not self.event.source.get("content", {}).get("membership") == "invite":
            raise EventNotConcerned

    async def only_allowed_sender(self, user_config) -> None:
        """
        :raise EventNotConcerned: if the sender is not allowed to send messages
        """
        if not self.is_sender_domain_allowed():
            await self.matrix_client.send_text_message(
                self.room.room_id,
                "Albert n'est pas encore disponible pour votre domaine. Merci de rester en contact, il sera disponible après un beta test.",
                msgtype="m.notice",
            )
            raise EventNotConcerned
        if not user_config.is_authorized(self.sender):
            await self.matrix_client.send_markdown_message(
                self.room.room_id,
                "Albert est en phase de test et n'est pas encore disponible pour votre utilisateur. Contactez albert-contact@data.gouv.fr pour demander un accès.",
                msgtype="m.notice",
            )
            raise EventNotConcerned


class MessageEventParser(EventParser):
    event: RoomMessageText

    def _command(self, command: str, prefix: str, body=None, command_name: str = "") -> str:
        command_prefix = f"{prefix}{command}"
        if body.split()[0] != command_prefix:
            raise EventNotConcerned
        command_payload = body.removeprefix(command_prefix)
        if self.log_usage:
            logger.info(
                "Handling command", command=command_name or command, command_payload=command_payload
            )
        return command_payload

    def command(self, command: str, prefix: str, command_name: str = "") -> str:
        """
        if the event is concerned by the command, returns the text after the command. Raise EventNotConcerned otherwise

        :param command: the command that is to be recognized.
        :param prefix: the prefix for this command (default is !).
        :param command_name: name of the command, for logging purposes.
        :return: the text after the command
        :raise EventNotConcerned: if the current event is not concerned by the command.
        """
        return self._command(
            command=command, prefix=prefix, command_name=command_name, body=self.event.body
        )

    async def hl(self, consider_hl_when_direct_message=True) -> str:
        """
        if the event is a hl (highlight, i.e begins with the name of the bot),
        returns the text after the hl. Raise EventNotConcerned otherwise

        :param consider_hl_when_direct_message: if True, consider a direct message as an highlight.
        :return: the text after the highlight
        :raise EventNotConcerned: if the current event is not concerned by the command.
        """
        display_name = await self.matrix_client.get_display_name()
        if consider_hl_when_direct_message and self.room_is_direct_message():
            return self._command(
                "",
                prefix="",
                body=self.event.body.removeprefix(display_name).removeprefix(": "),
                command_name="mention",
            )
        return self.command(display_name, prefix="", command_name="mention").removeprefix(": ")
