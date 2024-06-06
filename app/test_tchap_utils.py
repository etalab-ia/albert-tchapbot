# SPDX-FileCopyrightText: 2024 Etalab <etalab@modernisation.gouv.fr>
#
# SPDX-License-Identifier: MIT

from config import Config
from nio import MatrixRoom, MatrixUser, PowerLevels
from tchap_utils import (
    get_salon_moderators,
    get_salon_users_str,
    get_user_to_power_level,
    user_name_to_non_hl_user,
    users_print,
)


def test_get_user_to_power_level() -> None:
    user1 = MatrixUser(user_id="@alice:matrix.org", power_level=0)
    user2 = MatrixUser(user_id="@bob:matrix.org", power_level=50)
    user3 = MatrixUser(user_id="@charlie:matrix.org", power_level=100)
    salon = MatrixRoom(
        room_id="!room:matrix.org",
        own_user_id="@alice:matrix.org",
    )
    salon.users = {
        "@alice:matrix.org": user1,
        "@bob:matrix.org": user2,
        "@charlie:matrix.org": user3,
    }
    assert get_user_to_power_level(salon) == {
        "Alice": 0,
        "Bob": 50,
        "Charlie": 100,
    }
