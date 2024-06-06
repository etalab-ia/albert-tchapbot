# SPDX-FileCopyrightText: 2024 Etalab <etalab@modernisation.gouv.fr>
#
# SPDX-License-Identifier: MIT

from config import Config
from pyalbert_utils import (
    generate,
    generate_sources,
    get_available_modes,
    new_chat,
)


def test_get_available_modes() -> None:
    test_config = Config()
    assert len(get_available_modes(test_config)) > 0

    test_config = Config(albert_model_name="not_existing_model_name")
    assert get_available_modes(test_config) is None


def test_new_chat() -> None:
    test_config = Config()
    assert isinstance(new_chat(test_config), int)


def test_generate() -> None:
    test_config = Config()
    assert isinstance(generate(test_config, "Hello"), str)
    assert isinstance(test_config.albert_chat_id, int)
    assert isinstance(test_config.albert_stream_id, int)


def test_generate_sources() -> None:
    test_config = Config()
    generate(test_config, "Hello")
    assert isinstance(test_config.albert_stream_id, int)
    sources = generate_sources(test_config, test_config.albert_stream_id)
    assert isinstance(sources, list)
    assert len(sources) > 0
    assert isinstance(sources[0], dict)
    assert isinstance(sources[0].get("hash"), str)
    assert isinstance(sources[0].get("sid"), str)
    assert isinstance(sources[0].get("title"), str)
    assert isinstance(sources[0].get("url"), str)
    assert isinstance(sources[0].get("introduction"), str)
    assert isinstance(sources[0].get("text"), str)
    assert isinstance(sources[0].get("context"), str)
    assert isinstance(sources[0].get("surtitre"), str)
    assert isinstance(sources[0].get("source"), str)
