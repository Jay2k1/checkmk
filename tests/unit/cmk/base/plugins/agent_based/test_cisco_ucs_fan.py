#!/usr/bin/env python3
# Copyright (C) 2023 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from collections.abc import Sequence

import pytest

from cmk.base.legacy_checks.cisco_ucs_fan import check_cisco_ucs_fan, inventory_cisco_ucs_fan

STRING_TABLE = [
    ["sys/rack-unit-1/fan-module-1-1/fan-1", "1"],
    ["sys/rack-unit-1/fan-module-1-1/fan-2", "1"],
    ["sys/rack-unit-1/fan-module-1-2/fan-1", "1"],
    ["sys/rack-unit-1/fan-module-1-2/fan-2", "1"],
    ["sys/rack-unit-1/fan-module-1-3/fan-1", "1"],
    ["sys/rack-unit-1/fan-module-1-3/fan-2", "1"],
    ["sys/rack-unit-1/fan-module-1-4/fan-1", "1"],
    ["sys/rack-unit-1/fan-module-1-4/fan-2", "1"],
    ["sys/rack-unit-1/fan-module-1-5/fan-1", "1"],
    ["sys/rack-unit-1/fan-module-1-5/fan-2", "1"],
    ["sys/rack-unit-1/fan-module-1-6/fan-1", "1"],
    ["sys/rack-unit-1/fan-module-1-6/fan-2", "1"],
    ["sys/rack-unit-1/fan-module-1-7/fan-1", "1"],
    ["sys/rack-unit-1/fan-module-1-7/fan-2", "1"],
]


def test_discover_cisco_ucs_mem() -> None:
    assert list(inventory_cisco_ucs_fan(STRING_TABLE)) == [
        ("fan-module-1-1 fan-1", None),
        ("fan-module-1-1 fan-2", None),
        ("fan-module-1-2 fan-1", None),
        ("fan-module-1-2 fan-2", None),
        ("fan-module-1-3 fan-1", None),
        ("fan-module-1-3 fan-2", None),
        ("fan-module-1-4 fan-1", None),
        ("fan-module-1-4 fan-2", None),
        ("fan-module-1-5 fan-1", None),
        ("fan-module-1-5 fan-2", None),
        ("fan-module-1-6 fan-1", None),
        ("fan-module-1-6 fan-2", None),
        ("fan-module-1-7 fan-1", None),
        ("fan-module-1-7 fan-2", None),
    ]


@pytest.mark.parametrize(
    "item, expected_output",
    [
        pytest.param("missing", None, id="Item missing in data"),
        pytest.param(
            "fan-module-1-7 fan-2",
            (0, "Status: operable"),
            id="Last item in data",
        ),
    ],
)
def test_check_cisco_ucs_mem(item: str, expected_output: Sequence[object]) -> None:
    assert check_cisco_ucs_fan(item, None, STRING_TABLE) == expected_output
