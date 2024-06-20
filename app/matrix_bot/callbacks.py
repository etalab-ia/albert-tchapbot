# SPDX-FileCopyrightText: 2021 - 2022 Isaac Beverly <https://github.com/imbev>
# SPDX-FileCopyrightText: 2023 Pôle d'Expertise de la Régulation Numérique <contact.peren@finances.gouv.fr>
#
# SPDX-License-Identifier: MIT
from functools import wraps

from nio import (
    Event,
    InviteMemberEvent,
    MatrixRoom,
    MegolmEvent,
    RoomMessageText,
    ToDeviceEvent,
    UnknownEvent,
)

from .client import MatrixClient
from .config import logger
from .eventparser import (
    EventNotConcerned,
    EventParser,
    MessageEventParser,
)


def properly_fail(matrix_client):
    """use this decorator so that your async callback never crash, log the error and return a message to the room"""

    def decorator(func):
        @wraps(func)
        async def wrapper(room, event):
            try:
                return await func(room, event)
            except Exception as unexpected_exception:
                await matrix_client.send_text_message(room.room_id, "failed to answer")
                logger.warning(f"command failed with exception: {unexpected_exception}")
            finally:
                await matrix_client.room_typing(room.room_id, typing_state=False)

        return wrapper

    return decorator


def ignore_when_not_concerned(func):
    """decorator to use with async function using EventParser"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except EventNotConcerned:
            return

    return wrapper


class Callbacks:
    """A class for handling callbacks."""

    def __init__(self, matrix_client: MatrixClient):
        self.matrix_client = matrix_client
        self.startup = []
        self.client_callback = []

    def register_on_custom_event(self, func, onEvent: Event, feature: dict):
        @properly_fail(self.matrix_client)
        @ignore_when_not_concerned
        async def wrapped_func(room, event):
            if not isinstance(event, onEvent):
                raise EventNotConcerned

            if onEvent == RoomMessageText:
                ep = MessageEventParser(
                    room=room, event=event, matrix_client=self.matrix_client, log_usage=True
                )
                if feature.get("command"):
                    ep.command(feature["command"], prefix=feature["prefix"])
            else:
                ep = EventParser(
                    room=room, event=event, matrix_client=self.matrix_client, log_usage=True
                )

            ep.do_not_accept_own_message()  # avoid infinite loop
            await func(ep=ep, matrix_client=self.matrix_client)

        self.client_callback.append((wrapped_func, onEvent))

    def register_on_reaction_event(self, func):
        @properly_fail(self.matrix_client)
        @ignore_when_not_concerned
        async def wrapped_func(room: MatrixRoom, event: Event):
            if event.type == "m.reaction":
                await func(room, event, event.source["content"]["m.relates_to"]["key"])

        self.client_callback.append((wrapped_func, UnknownEvent))

    def register_on_startup(self, func):
        self.startup.append(func)

    async def setup_callbacks(self):
        """Add callbacks to async_client"""
        self.matrix_client.add_event_callback(self.invite_callback, InviteMemberEvent)

        self.matrix_client.add_event_callback(self.decryption_failure, MegolmEvent)

        for function, event in self.client_callback:
            if issubclass(event, ToDeviceEvent):
                self.matrix_client.add_to_device_callback(function, event)
            else:
                self.matrix_client.add_event_callback(function, event)

    async def invite_callback(self, room: MatrixRoom, event: InviteMemberEvent):
        """Callback for handling invites."""
        if not event.membership == "invite":
            return

        try:
            await self.matrix_client.join(room.room_id)
            logger.info(f"Joined {room.room_id}")
        except Exception as join_room_exception:
            logger.info(f"Failed to join {room.room_id}", join_room_exceptions=join_room_exception)

    async def decryption_failure(self, room: MatrixRoom, event: MegolmEvent):
        """Callback for handling decryption errors."""
        if not isinstance(event, MegolmEvent):
            return

        logger.error(
            f"Failed to decrypt message: {event.event_id} from {event.sender} in {room.room_id}. "
            "If this error persists despite verification, reset the crypto session by deleting "
            f"{self.matrix_client.matrix_config.store_path} and {self.matrix_client.auth.session_stored_file_path}. "
            "You will have to verify any verified devices anew."
        )
        await self.matrix_client.send_text_message(
            room.room_id,
            "Failed to decrypt your message. Make sure encryption is enabled in my config and "
            "either enable sending messages to unverified devices or verify me if possible.",
            msgtype="m.notice",
        )
