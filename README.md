<!--
SPDX-FileCopyrightText: 2023 Pôle d'Expertise de la Régulation Numérique <contact.peren@finances.gouv.fr>
SPDX-FileCopyrightText: 2024 Etalab <etalab@modernisation.gouv.fr>

SPDX-License-Identifier: MIT
-->

# Albert Tchap

*[English version below](#english-version)*

| <a href="https://github.com/etalab-ia/albert"><b>Albert API sur GitHub</b></a> | <a href="https://huggingface.co/AgentPublic"><b>Modèles Albert sur HuggingFace</b></a> |

## Description du projet

Bot pour [Tchap, l'application de messagerie de l'administration française](https://tchap.beta.gouv.fr/).
Ce bot utilise [Albert](https://github.com/etalab-ia/albert), l'agent conversationnel (*large language models*, LLM) de l'administration française, pour répondre à des questions sur [Tchap, l'application de messagerie de l'administration française](https://tchap.beta.gouv.fr/).

Le projet est un POC (Proof of Concept - preuve de concept) pour montrer comment un bot peut être utilisé pour répondre à des questions sur Tchap en utilisant Albert.
Il s'agit d'un travail WIP (Work In Progress - en cours de développement) et n'est pas (encore) destiné à être utilisé en production.

Le projet est un fork de [tchap_bot](https://code.peren.fr/open-source/tchapbot) qui est un bot Matrix pour Tchap, conçu par le [Pôle d'Expertise de la Régulation Numérique](https://www.peren.gouv.fr/). La partie bibliothèque (`matrix_bot`) est fortement inspirée de https://github.com/imbev/simplematrixbotlib.

Contient :
- `app/.` : la codebase pour le Tchap bot Albert
- `app/matrix_bot` : une bibliothèque pour pouvoir faire des bots Matrix


### Installation locale

Le projet utilise un fichier de dépendances et de config `pyproject.toml` et non un fichier `requirements.txt`. Il est donc nécessaire d'utiliser `pip` en version 19.0 ou supérieure, ou bien avec un package manager comme `pdm`, `pip-tools`, `uv`, `rye`, `hatch` etc. (mais pas `poetry` qui n'utilise pas le standard `pyproject.toml`).

```bash
# Récupération du code avec Git
git clone ${GITHUB_URL}

# Création d'un environnement virtuel Python
python3 -m venv .venv

# Activation de l'environnement virtuel Python
source .venv/bin/activate

# Installation des dépendances
pip install .
```


### Configuration

Créez le fichier d'environnement `app/.env` avec les informations de connexion (ou fournissez-les en variables d'environnement). Vous pouvez vous inspirer du fichier `app/.env.example` qui est initialisé avec les valeurs par défaut :
```bash
cp app/.env.example app/.env
```

Les variables d'environnement à renseigner sont les suivantes :

- `SALT` : il est conseillé de changer la valeur du salt pour ne pas avoir celle par défaut. Il faudra en revanche qu'elle de change pas entre deux sessions.
- `MATRIX_HOME_SERVER` : l'URL du serveur Matrix à utiliser (exemple : `MATRIX_HOME_SERVER="https://matrix.agent.ministere_example.tchap.gouv.fr"`)
- `MATRIX_BOT_USERNAME` : le nom d'utilisateur du bot Matrix (exemple : `MATRIX_BOT_USERNAME="tchapbot@ministere_example.gouv.fr"`)
- `MATRIX_BOT_PASSWORD` : le mot de passe du bot Matrix
- `ERRORS_ROOM_ID` : l'identifiant du salon Tchap où les erreurs seront envoyées (exemple : `ERRORS_ROOM_ID="!roomid:matrix.agent.ministere_example.tchap.gouv.fr"`). **Attention** : le bot doit être invité dans ce salon pour pouvoir y envoyer ses messages d'erreur !

Pour que le bot se connecte à l'API d'Albert, il faut également renseigner les variables suivantes :
- `USER_ALLOWED_DOMAINS` : liste des domaines d'email autorisés pour les utilisateurs Tchap pour qu'ils puissent interagir avec le bot (exemple : `USER_ALLOWED_DOMAINS='["ministere1.gouv.fr", "ministere2.gouv.fr"]'`. Par défaut : `["*"]` (tous les domaines sont autorisés))
- `GROUPS_USED=['albert']` : permet, dans cet exemple, d'activer toutes les commandes qui font partie du groupe "albert"
- `ALBERT_API_URL` : l'url de l'API Albert à consommer
- `ALBERT_API_TOKEN` : le token API utilisé pour authoriser le bot a consommer l'API Albert. Pour plus d'informations, consultez la documentation de l'API Albert
- `ALBERT_MODEL_NAME` : le nom du modèle Albert à utiliser pour le bot (exemple : `ALBERT_MODEL_NAME='AgentPublic/albertlight-7b'`). Pour plus d'informations, consultez la documentation de l'API Albert et le [hub des modèles Albert de HuggingFace](https://huggingface.co/collections/AgentPublic/albert-662a1d95c93a47aca5cecc82)
- `ALBERT_MODE` : le mode d'Albert à utiliser pour le bot (exemple : `ALBERT_MODE='rag'`). Pour plus d'informations, consultez la documentation de l'API Albert
- `CONVERSATION_OBSOLESCENCE` : le temps en secondes après lequel une conversation se remet automatiquement à zéro (exemple : `CONVERSATION_OBSOLESCENCE=3600` pour une heure). Par défaut : `3600` (une heure)


### Utilisation en dehors de Docker

Pour lancer le bot en dehors de Docker :
```bash
cd app
./.venv/bin/python3 .
```


### Utilisation avec Docker

1. Créez un fichier `.env` à la racine du projet avec les variables d'environnement mentionnées dans [app/.env.example](./app/.env.example) y compris celles mentionnées dans la section *"For docker-compose deployment"*

2. Lancer le container du bot à la racine du projet :
```bash
docker compose up --detach
```


### Troubleshooting

Le premier sync est assez long, et a priori non bloquant. Si vous avez une interaction avec le bot avant qu'il se soit bien sync vous risquez de le laisser dans un état instable (où le bot n'a pas le listing des rooms).


### Contribution

Le projet est en open source, sous [licence MIT](LICENSES/MIT.txt). Toutes les contributions sont bienvenues, sous forme de pull requests ou d'ouvertures d'issues sur le [repo officiel GitHub](https://github.com/etalab-ia/albert-tchapbot).

Avant de contribuer au dépôt, il est nécessaire d'initialiser les _hooks_ de _pre-commit_ :
```bash
pre-commit install
```

Si vous ne pouvez pas utiliser de pre-commit, il est nécessaire de formatter, linter et trier les imports avec [Ruff](https://docs.astral.sh/ruff/) :
```bash
ruff check --fix --select I .
```


### Licence

Ce projet est sous licence MIT. Une copie intégrale du texte de la licence se trouve dans le fichier [`LICENSES/MIT.txt`](LICENSES/MIT.txt).


---

# English version

<details>
  <summary>English version</summary>


| <a href="https://github.com/etalab-ia/albert"><b>Albert API on GitHub</b></a> | <a href="https://huggingface.co/AgentPublic"><b>Albert models on HuggingFace</b></a> |

## Project Description

Bot for [Tchap, the French government messaging application](https://tchap.beta.gouv.fr/).
This bot uses [Albert](https://github.com/etalab-ia/albert), the conversational agent (large language models, LLM) of the French government, to answer questions about [Tchap](https://tchap.beta.gouv.fr/).

The project is a Proof of Concept (POC) to show how a bot can be used to answer questions about Tchap using Albert.
It is a Work In Progress (WIP) and is not (yet) intended for production use.

The project is a fork of [tchap_bot](https://code.peren.fr/open-source/tchapbot) which is a Matrix bot for Tchap, designed by the [Pôle d'Expertise de la Régulation Numérique](https://www.peren.gouv.fr/). The library part (`matrix_bot`) is heavily inspired by https://github.com/imbev/simplematrixbotlib.

Contains:
- `app/.`: the codebase for the Albert Tchap bot
- `app/matrix_bot`: a library to be able to make Matrix bots


### Local Installation

The project uses a dependencies and config file `pyproject.toml` and not a `requirements.txt` file. It is therefore necessary to use `pip` in version 19.0 or higher, or with a package manager like `pdm`, `pip-tools`, `uv`, `rye`, `hatch` etc. (but not `poetry` which does not use the standard `pyproject.toml`).

```bash
# Getting the code with Git
git clone ${GITHUB_URL}

# Creating a Python virtual environment
python3 -m venv .venv

# Activating the Python virtual environment
source .venv/bin/activate

# Installing dependencies
pip install .
```

### Configuration

Create the environment file `app/.env` with the connection information (or provide them as environment variables). You can use the `app/.env.example` file as inspiration, which is initialized with default values:
```bash
cp app/.env.example app/.env
```

The following environment variables must be entered:

- `SALT`: it is advisable to change the salt value to avoid having the default one. However, it must not change between sessions.
- `MATRIX_HOME_SERVER`: the URL of the Matrix server to be used (example: `MATRIX_HOME_SERVER=“https://matrix.agent.ministere_example.tchap.gouv.fr”`).
- `MATRIX_BOT_USERNAME`: the Matrix bot username (example: `MATRIX_BOT_USERNAME=“tchapbot@ministere_example.gouv.fr”`)
- `MATRIX_BOT_PASSWORD`: the Matrix bot user password
- `ERRORS_ROOM_ID`: the Tchap room ID where errors will be sent (example: `ERRORS_ROOM_ID=“!roomid:matrix.agent.ministere_example.tchap.gouv.fr”`). **Warning**: the bot must be invited to this room to be able to send error messages!

For the bot to connect to Albert API, you also need to provide the following variables:
- `USER_ALLOWED_DOMAINS`: list of allowed email domains for Tchap users to interact with the bot (example: `USER_ALLOWED_DOMAINS='["ministere.gouv.fr"]'`. Default: `["*"]` (all domains are allowed))
- `GROUPS_USED=['albert']`: allows, in this example, to activate all commands that are part of the albert group
- `ALBERT_API_URL`: the URL of the Albert API to consume
- `ALBERT_API_TOKEN`: the API token used to authorize the bot to consume the Albert API. For more info, check the Albert API documentation
- `ALBERT_MODEL_NAME`: the name of the model to use for the bot (example: `ALBERT_MODEL_NAME='AgentPublic/albertlight-7b'`). For more info, check the Albert API documentation and the [Albert models hub on HuggingFace](https://huggingface.co/collections/AgentPublic/albert-662a1d95c93a47aca5cecc82).
- `ALBERT_MODE`: the mode of Albert to use for the bot (example: `ALBERT_MODE='rag'`). For more info, check the Albert API documentation
- `CONVERSATION_OBSOLESCENCE` : the time in seconds after which a conversation automatically resets (example: `CONVERSATION_OBSOLESCENCE=3600` for one hour). Default: `3600` (one hour)

### Usage outside of Docker

To launch the bot outside of Docker:
```bash
cd app
./.venv/bin/python3 .
```

### Usage with Docker

1. Create a `.env` file at the root of the project with the environment variables mentioned in [app/.env.example](./app/.env.example), including those mentionned in the *"For docker-compose deployment"* section

2. Launch the bot container at the root of the project:
```bash
docker compose up --detach
```

### Troubleshooting

The first sync is quite long, and apparently non-blocking. If you interact with the bot before it has synced properly, you risk leaving it in an unstable state (where the bot does not have the room listing).

### Contribution

This project is open source, under the [MIT license](LICENSES/MIT.txt). All contributions are welcome, in the form of pull requests or issue openings on the [repo officiel GitHub](https://github.com/etalab-ia/albert-tchapbot).

Before contributing to the repository, it is necessary to initialize the pre-commit hooks:
```bash
pre-commit install
```

If you cannot use pre-commit, it is necessary to format, lint, and sort imports with [Ruff](https://docs.astral.sh/ruff/) before committing:
```bash
ruff check --fix --select I .
```

### License

This project is licensed under the MIT License. A full copy of the license text can be found in the `LICENSES/MIT.txt` file.

</details>
