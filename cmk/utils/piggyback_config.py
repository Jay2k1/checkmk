#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.
import re
from collections.abc import Iterable, Sequence
from contextlib import suppress
from typing import Final

from cmk.utils.hostaddress import HostAddress

_HostCondition = str | None
_KeyName = str  # 'max_cache_age', 'validity_period', 'validity_state'
_Value = int

PiggybackTimeSettings = Sequence[tuple[_HostCondition, _KeyName, _Value]]


class Config:
    def __init__(
        self,
        piggybacked_hostname: HostAddress,
        time_settings: PiggybackTimeSettings,
    ) -> None:
        self.piggybacked: Final = piggybacked_hostname
        self._expanded_settings = {
            (host, key): value
            for expr, key, value in reversed(time_settings)
            for host in self._normalize_pattern(expr, piggybacked_hostname)
        }

    @staticmethod
    def _normalize_pattern(
        expr: str | None, piggybacked: HostAddress
    ) -> Iterable[HostAddress | None]:
        # expr may be
        #   - None (global settings) or
        #   - 'source-hostname' or
        #   - 'piggybacked-hostname' or
        #   - '~piggybacked-[hH]ostname'
        # the first entry ('piggybacked-hostname' vs '~piggybacked-[hH]ostname') wins
        if expr is None:
            yield None
        elif not expr.startswith("~"):
            yield HostAddress(expr)
        elif re.match(expr[1:], piggybacked):
            yield piggybacked

    def _match(self, key: str, source_hostname: HostAddress) -> int:
        with suppress(KeyError):
            return self._expanded_settings[(self.piggybacked, key)]
        with suppress(KeyError):
            return self._expanded_settings[(source_hostname, key)]
        return self._expanded_settings[(None, key)]

    def max_cache_age(self, source: HostAddress) -> int:
        return self._match("max_cache_age", source)

    def validity_period(self, source: HostAddress) -> int:
        try:
            return self._match("validity_period", source)
        except KeyError:
            return 0

    def validity_state(self, source: HostAddress) -> int:
        try:
            return self._match("validity_state", source)
        except KeyError:
            return 0
