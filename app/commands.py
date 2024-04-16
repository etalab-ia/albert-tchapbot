# SPDX-FileCopyrightText: 2023 Pôle d'Expertise de la Régulation Numérique <contact.peren@finances.gouv.fr>
#
# SPDX-License-Identifier: MIT

import datetime
from dataclasses import dataclass

from nio import MatrixRoom, Event

from albert_client import AlbertApiClient
from matrix_bot.callbacks import properly_fail
from matrix_bot.client import MatrixClient
from matrix_bot.config import logger
from matrix_bot.eventparser import MessageEventParser, ignore_when_not_concerned
from config import env_config, COMMAND_PREFIX


@dataclass
class CommandRegistry:
    function_register: dict
    activated_functions: set[str]

    def add_command(self, *, name: str, help: str | None, group: str, func):
        self.function_register[name] = {"help": help, "group": group, "func": func}

    def get_help(self) -> list[str]:
        return [
            function["help"]
            for name, function in self.function_register.items()
            if name in self.activated_functions and function["help"]
        ]

    def activate_and_retrieve_group(self, group_name: str):
        self.activated_functions |= {
            name
            for name, function in self.function_register.items()
            if function["group"] == group_name
        }
        return [
            function["func"]
            for name, function in self.function_register.items()
            if function["group"] == group_name
        ]


command_registry = CommandRegistry({}, set())


def register_feature(help: str | None, group: str):
    def decorator(func):
        command_registry.add_command(name=func.__name__, help=help, group=group, func=func)
        return func

    return decorator


@register_feature(help=f"**{COMMAND_PREFIX}aide** : donne l'aide", group="basic")
@properly_fail
@ignore_when_not_concerned
async def help(room: MatrixRoom, message: Event, matrix_client: MatrixClient):
    event_parser = MessageEventParser(room=room, event=message, matrix_client=matrix_client)
    event_parser.do_not_accept_own_message()
    help_message = "Les commandes sont :\n - " + "\n - ".join(command_registry.get_help())
    event_parser.command("aide", prefix=COMMAND_PREFIX)
    logger.info("Handling command", command="help")
    await matrix_client.room_typing(room.room_id)
    await matrix_client.send_markdown_message(room.room_id, help_message)


@register_feature(help="**{COMMAND_PREFIX}heure** : donne l'heure", group="utils")
@properly_fail
@ignore_when_not_concerned
async def heure(room: MatrixRoom, message: Event, matrix_client: MatrixClient):
    event_parser = MessageEventParser(room=room, event=message, matrix_client=matrix_client)
    event_parser.do_not_accept_own_message()
    event_parser.command("heure", prefix=COMMAND_PREFIX)
    heure = f"il est {datetime.datetime.now().strftime('%Hh%M')}"
    logger.info("Handling command", command="heure")
    await matrix_client.room_typing(room.room_id)
    await matrix_client.send_text_message(room.room_id, heure)


@register_feature(
    help=f"**{COMMAND_PREFIX}reset** : recommence un stream avec Albert", group="albert"
)
@properly_fail
@ignore_when_not_concerned
async def albert_reset(room: MatrixRoom, message: Event, matrix_client: MatrixClient):
    event_parser = MessageEventParser(room=room, event=message, matrix_client=matrix_client)
    event_parser.do_not_accept_own_message()
    event_parser.command("reset", prefix="!")
    # TODO: Albert reset stream
    reset: str = "La conversation a été remise à zéro."
    logger.info("Handling command", command="reset")
    await matrix_client.room_typing(room.room_id)
    await matrix_client.send_text_message(room.room_id, reset)


@register_feature(help=None, group="albert")
@properly_fail
@ignore_when_not_concerned
async def albert_answer(room: MatrixRoom, message: Event, matrix_client: MatrixClient):
    """
    Send the prompt to Albert and return the response
    """
    event_parser = MessageEventParser(
        room=room, event=message, matrix_client=matrix_client, log_usage=True
    )
    event_parser.do_not_accept_own_message()
    user_prompt: str = await event_parser.hl()
    if user_prompt[0] != COMMAND_PREFIX:
        await matrix_client.room_typing(room.room_id, typing_state=True, timeout=180_000)
        try:
            albert_api_client = AlbertApiClient(config=env_config)
        except Exception as albert_exception:
            logger.error(f"Albert API client instanciation failed with {albert_exception=}")
        else:

            # TODO: send the prompt as a HTTP request to Albert and get the response, using albert_api_client instance
            # TODO: send the response to the room

            await matrix_client.send_text_message(
                room.room_id, f"Pour remettre à zéro la conversation, tapez `{COMMAND_PREFIX}reset`"
            )  # TODO
            pass

            ALBERT_ERROR_RESPONSE = "Albert n'est pas configuré. Contactez albert-contact@data.gouv.fr pour signaler cette erreur."
            logger.info(f"{ALBERT_ERROR_RESPONSE=}")
            try:  # sometimes the async code fail (when input is big) with random asyncio errors
                await matrix_client.send_text_message(room.room_id, ALBERT_ERROR_RESPONSE)
            except Exception as llm_exception:  # it seems to work when we retry
                logger.error(f"Albert API response failed with {llm_exception=}. retrying")
                await matrix_client.send_text_message(room.room_id, ALBERT_ERROR_RESPONSE)

