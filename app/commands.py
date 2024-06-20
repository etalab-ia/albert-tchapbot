# SPDX-FileCopyrightText: 2023 Pôle d'Expertise de la Régulation Numérique <contact.peren@finances.gouv.fr>
# SPDX-FileCopyrightText: 2024 Etalab <etalab@modernisation.gouv.fr>
#
# SPDX-License-Identifier: MIT

from collections import defaultdict
from dataclasses import dataclass

from config import APP_VERSION, COMMAND_PREFIX, Config
from matrix_bot.client import MatrixClient
from matrix_bot.config import bot_lib_config, logger
from matrix_bot.eventparser import EventNotConcerned, EventParser
from nio import Event, RoomMemberEvent, RoomMessageText
from pyalbert_utils import (
    generate,
    generate_sources,
    get_available_models,
    get_available_modes,
    new_chat,
)


@dataclass
class CommandRegistry:
    function_register: dict
    activated_functions: set[str]

    def add_command(
        self,
        name: str,
        group: str,
        onEvent: Event,
        command: str | None,
        prefix: str | None,
        help_message: str | None,
        hidden: bool,
        func,
    ):
        self.function_register[name] = {
            "name": name,
            "group": group,
            "onEvent": onEvent,
            "command": command,
            "prefix": prefix,
            "help": help_message,
            "hidden": hidden,
            "func": func,
        }

    def activate_and_retrieve_group(self, group_name: str) -> list:
        features = []
        for name, feature in self.function_register.items():
            if feature["group"] == group_name:
                self.activated_functions |= {name}
                features.append(feature)
        return features

    def is_valid_command(self, command) -> bool:
        return command in [
            feature["command"]
            for name, feature in self.function_register.items()
            if name in self.activated_functions
        ]

    def get_help(self, config: Config) -> str:
        cmds = self._get_cmds(config)

        model_url = f"https://huggingface.co/{config.albert_model_name}"
        model_short_name = config.albert_model_name.split("/")[-1]

        help_message = "👋 Bonjour, je suis **Albert**, votre **assistant automatique dédié aux questions légales et administratives** mis à disposition par la **DINUM**. Je suis actuellement en phase de **test**.\n\n"
        help_message += f"J'utilise le modèle de langage _[{model_short_name}]({model_url})_ et j'ai été alimenté par des bases de connaissances gouvernementales, comme les fiches pratiques de service-public.fr éditées par la Direction de l'information légale et administrative (DILA).\n\n"

        help_message += "Maintenant que nous avons fait plus connaissance, quelques **règles pour m'utiliser** :\n\n"

        help_message += (
            "🔮 Ne m'utilisez pas pour élaborer une décision administrative individuelle.\n\n"
        )
        help_message += "❌ **Ne me transmettez pas** :\n"
        help_message += "- des **fichiers** (pdf, images, etc.) ;\n"
        help_message += (
            "- des données permettant de **vous** identifier ou **d'autres personnes** ;\n"
        )
        help_message += "- des données **confidentielles** ;\n\n"

        help_message += "Enfin, quelques informations pratiques :\n\n"

        help_message += "🛠️ **Pour gérer notre conversation** :\n"
        help_message += "- " + "\n- ".join(cmds)
        help_message += "\n\n"

        help_message += "📁 **Sur l'usage des données**\nLes conversations sont stockées de manière anonyme. Elles me permettent de contextualiser les conversations et l'équipe qui me développe les utilise pour m'évaluer et analyser mes performances.\n\n"

        help_message += "📯 Nous contacter : albert-contact@data.gouv.fr"

        return help_message

    def show_commands(self, config: Config) -> str:
        cmds = self._get_cmds(config)
        available_cmd = "Les commandes spéciales suivantes sont disponibles :\n\n"
        available_cmd += "- " + "\n- ".join(cmds)
        return available_cmd

    def _get_cmds(self, config: Config) -> list[str]:
        cmds = set(
            feature["help"]
            for name, feature in self.function_register.items()
            if name in self.activated_functions
            and feature["help"]
            and not feature["hidden"]
            and not (feature.get("command") == "sources" and config.albert_mode == "norag")
        )
        return sorted(list(cmds))


command_registry = CommandRegistry({}, set())
user_configs = defaultdict(lambda: Config())


def register_feature(
    group: str,
    onEvent: Event,
    command: str | None = None,
    prefix: str = COMMAND_PREFIX,
    help: str | None = None,
    hidden: bool = False,
):
    def decorator(func):
        command_registry.add_command(
            name=func.__name__,
            group=group,
            onEvent=onEvent,
            command=command,
            prefix=prefix,
            help_message=help,
            hidden=hidden,
            func=func,
        )
        return func

    return decorator


@register_feature(
    group="basic",
    onEvent=RoomMessageText,
    command="aide",
    help=f"Pour retrouver ce message informatif, utilisez **{COMMAND_PREFIX}aide**",
)
async def help(ep: EventParser, matrix_client: MatrixClient):
    config = user_configs[ep.sender]
    await ep.only_allowed_sender(config)
    await matrix_client.room_typing(ep.room.room_id)
    await matrix_client.send_markdown_message(ep.room.room_id, command_registry.get_help(config))


@register_feature(
    group="albert",
    onEvent=RoomMessageText,
    command="reset",
    help=f"Pour ré-initialiser notre conversation, utilisez **{COMMAND_PREFIX}reset**",
)
async def albert_reset(ep: EventParser, matrix_client: MatrixClient):
    config = user_configs[ep.sender]
    await ep.only_allowed_sender(config)
    if config.albert_with_history:
        config.update_last_activity(ep.sender)
        await matrix_client.room_typing(ep.room.room_id)
        config.albert_chat_id = new_chat(config)
        reset_message = "**La conversation a été remise à zéro.**\n\n"
        reset_message += command_registry.show_commands(config)
        await matrix_client.send_markdown_message(
            ep.room.room_id, reset_message, msgtype="m.notice"
        )


@register_feature(
    group="albert",
    onEvent=RoomMessageText,
    command="conversation",
    help=f"Pour activer/désactiver le mode conversation, utilisez **{COMMAND_PREFIX}conversation**",
    hidden=True,
)
async def albert_conversation(ep: EventParser, matrix_client: MatrixClient):
    config = user_configs[ep.sender]
    await ep.only_allowed_sender(config)
    await matrix_client.room_typing(ep.room.room_id)
    if config.albert_with_history:
        config.albert_with_history = False
        config.albert_chat_id = None
        message = "Le mode conversation est désactivé."
    else:
        config.update_last_activity(ep.sender)
        config.albert_with_history = True
        message = "Le mode conversation est activé."
    await matrix_client.send_text_message(ep.room.room_id, message)


@register_feature(
    group="albert",
    onEvent=RoomMessageText,
    command="debug",
    help=f"Pour afficher des informations sur la configuration actuelle, **{COMMAND_PREFIX}debug**",
    hidden=True,
)
async def albert_debug(ep: EventParser, matrix_client: MatrixClient):
    config = user_configs[ep.sender]
    await ep.only_allowed_sender(config)
    await matrix_client.room_typing(ep.room.room_id)
    debug_message = f"Configuration actuelle :\n\n"
    debug_message += f"- Version: {APP_VERSION}\n"
    debug_message += f"- API: {config.albert_api_url}\n"
    debug_message += f"- Model: {config.albert_model_name}\n"
    debug_message += f"- Mode: {config.albert_mode}\n"
    debug_message += f"- With history: {config.albert_with_history}\n"
    debug_message += f"- Chat ID: {config.albert_chat_id}\n"
    debug_message += f"- Stream ID: {config.albert_stream_id}\n"
    await matrix_client.send_markdown_message(ep.room.room_id, debug_message)


@register_feature(
    group="albert",
    onEvent=RoomMessageText,
    command="model",
    help=f"Pour modifier le modèle, utilisez **{COMMAND_PREFIX}model** MODEL_NAME",
    hidden=True,
)
async def albert_model(ep: EventParser, matrix_client: MatrixClient):
    config = user_configs[ep.sender]
    await matrix_client.room_typing(ep.room.room_id)
    commands = ep.event.body.split()
    # Get all available models
    all_models = get_available_models(config)
    if len(commands) <= 1:
        message = (
            f"La commande !model nécessite de donner un modèle parmi : {', '.join(all_models)}"
        )
    else:
        model = commands[1]
        if model not in all_models:
            message = f"Modèle inconnu. Les modèles disponibles sont : {', '.join(all_models)}"
        else:
            previous_model = config.albert_model_name
            config.albert_model_name = model
            message = f"Le modèle a été modifié : {previous_model} -> {model}"
    await matrix_client.send_text_message(ep.room.room_id, message)


@register_feature(
    group="albert",
    onEvent=RoomMessageText,
    command="mode",
    help=f"Pour modifier le mode du modèle (c'est-à-dire le modèle de prompt utilisé), utilisez **{COMMAND_PREFIX}mode** MODE",
    hidden=True,
)
async def albert_mode(ep: EventParser, matrix_client: MatrixClient):
    config = user_configs[ep.sender]
    await ep.only_allowed_sender(config)
    await matrix_client.room_typing(ep.room.room_id)
    commands = ep.event.body.split()
    # Get all available mode for the current model
    all_modes = get_available_modes(config)
    all_modes += ["norag"]
    if len(commands) <= 1:
        message = f"La commande !mode nécessite de donner un mode parmi : {', '.join(all_modes)}"
    else:
        mode = commands[1]
        if mode not in all_modes:
            message = f"Mode inconnu. Les modes disponibles sont : {', '.join(all_modes)}"
        else:
            old_mode = config.albert_mode
            config.albert_mode = mode
            message = f"Le mode a été modifié : {old_mode} -> {mode}"
    await matrix_client.send_text_message(ep.room.room_id, message)


@register_feature(
    group="albert",
    onEvent=RoomMessageText,
    command="sources",
    help=f"Pour obtenir les sources utilisées pour générer ma dernière réponse, utilisez **{COMMAND_PREFIX}sources**",
)
async def albert_sources(ep: EventParser, matrix_client: MatrixClient):
    config = user_configs[ep.sender]
    await ep.only_allowed_sender(config)
    await matrix_client.room_typing(ep.room.room_id)
    try:
        if config.albert_stream_id:
            sources = generate_sources(config=config, stream_id=config.albert_stream_id)
            sources_msg = ""
            for source in sources:
                extra_context = ""
                if source.get("context"):
                    extra_context = f'({source["context"]})'
                sources_msg += f'- {source["title"]} {extra_context}: {source["url"]} \n'
        else:
            sources_msg = "Aucune source trouvée, veuillez me poser une question d'abord."
    except Exception as albert_exception:
        await matrix_client.send_markdown_message(
            ep.room.room_id, f"\u26a0\ufe0f **Serveur erreur**\n\n{albert_exception}"
        )
        return

    await matrix_client.send_text_message(ep.room.room_id, sources_msg)


@register_feature(
    group="albert",
    onEvent=RoomMessageText,
    help=None,
)
async def albert_answer(ep: EventParser, matrix_client: MatrixClient):
    """
    Receive a message event which is not a command, send the prompt to Albert API and return the response to the user
    """
    config = user_configs[ep.sender]
    await ep.only_allowed_sender(config)

    # If the user has never used Albert, we send the help message
    if not config.has_activity(ep.sender):
        config.update_last_activity(ep.sender)
        await matrix_client.room_typing(ep.room.room_id)
        await matrix_client.send_markdown_message(
            ep.room.room_id, command_registry.get_help(config)
        )
        # Redirect the error message to the errors room if it exists
        if config.errors_room_id:
            await matrix_client.send_markdown_message(
                config.errors_room_id,
                f"\u26a0\ufe0f **New Albert Tchap user access request**\n\n{ep.sender}\n\nMatrix server: {config.matrix_home_server}",
            )

    user_prompt = ep.event.body
    if user_prompt.startswith(COMMAND_PREFIX):
        raise EventNotConcerned

    ep.only_on_direct_message()
    query = user_prompt

    if config.albert_with_history and config.is_conversation_obsolete:
        config.albert_chat_id = new_chat(config)
        obsolescence_in_minutes = str(bot_lib_config.conversation_obsolescence // 60)
        reset_message = f"Comme vous n'avez pas continué votre conversation avec Albert depuis plus de {obsolescence_in_minutes} minutes, **la conversation a été automatiquement remise à zéro.**\n\n"
        reset_message += command_registry.show_commands(config)
        await matrix_client.room_typing(ep.room.room_id)
        await matrix_client.send_markdown_message(
            ep.room.room_id, reset_message, msgtype="m.notice"
        )

    config.update_last_activity(ep.sender)
    await matrix_client.room_typing(ep.room.room_id, typing_state=True, timeout=180_000)
    try:
        answer = generate(config=config, query=query)
    except Exception as albert_exception:
        # Send an error message to the user
        await matrix_client.send_markdown_message(
            ep.room.room_id,
            f"\u26a0\ufe0f **Erreur**\n\nAlbert est actuellement en maintenance, étant encore en phase de test. Réessayez plus tard.",
        )
        # Redirect the error message to the errors room if it exists
        if config.errors_room_id:
            await matrix_client.send_markdown_message(
                config.errors_room_id,
                f"\u26a0\ufe0f **Albert API erreur**\n\n{albert_exception}\n\nMatrix server: {config.matrix_home_server}",
            )
        return

    logger.debug(f"{query=}")
    logger.debug(f"{answer=}")
    try:  # sometimes the async code fail (when input is big) with random asyncio errors
        await matrix_client.send_markdown_message(ep.room.room_id, answer)
    except Exception as llm_exception:  # it seems to work when we retry
        logger.error(f"asyncio error when sending message {llm_exception=}. retrying")
        await matrix_client.send_markdown_message(ep.room.room_id, answer)


@register_feature(
    group="albert",
    onEvent=RoomMessageText,
    help=None,
)
async def albert_wrong_command(ep: EventParser, matrix_client: MatrixClient):
    config = user_configs[ep.sender]
    user_prompt = ep.event.body
    command = user_prompt.split()[0][1:]
    if not user_prompt.startswith(COMMAND_PREFIX) or command_registry.is_valid_command(command):
        raise EventNotConcerned
    await matrix_client.send_markdown_message(
        ep.room.room_id,
        f"\u26a0\ufe0f **Commande inconnue**\n\n{command_registry.show_commands(config)}",
    )
