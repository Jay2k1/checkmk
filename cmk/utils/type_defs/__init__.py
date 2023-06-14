#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.
"""Checkmk wide type definitions"""

__all__ = [
    "ValidatedString",
    "ActiveCheckPluginName",
    "AgentRawData",
    "CheckPluginNameStr",
    "ClusterMode",
    "ContactgroupName",
    "Deserializer",
    "DiscoveryResult",
    "EvalableFloat",
    "EVERYTHING",
    "ExitSpec",
    "ensure_mrpe_configs",
    "HostAddress",
    "HostgroupName",
    "HostName",
    "HostOrServiceConditionRegex",
    "HostOrServiceConditions",
    "HostOrServiceConditionsNegated",
    "HostOrServiceConditionsSimple",
    "HostState",
    "InfluxDBConnectionSpec",
    "Item",
    "JsonSerializable",
    "LegacyCheckParameters",
    "MrpeConfig",
    "MrpeConfigDeprecated",
    "MetricName",
    "MetricTuple",
    "ParametersTypeAlias",
    "ParsedSectionName",
    "RuleSetName",
    "Seconds",
    "SectionName",
    "Serializer",
    "ServiceAdditionalDetails",
    "ServiceDetails",
    "ServicegroupName",
    "ServiceName",
    "ServiceState",
    "SNMPDetectBaseType",
    "state_markers",
    "TimeRange",
    "Timestamp",
    "UserId",
]


from ._misc import (
    ActiveCheckPluginName,
    AgentRawData,
    CheckPluginNameStr,
    ClusterMode,
    ContactgroupName,
    DiscoveryResult,
    EvalableFloat,
    EVERYTHING,
    ExitSpec,
    HostOrServiceConditionRegex,
    HostOrServiceConditions,
    HostOrServiceConditionsNegated,
    HostOrServiceConditionsSimple,
    InfluxDBConnectionSpec,
    Item,
    JsonSerializable,
    LegacyCheckParameters,
    MetricName,
    MetricTuple,
    ParametersTypeAlias,
    Seconds,
    ServiceAdditionalDetails,
    ServiceDetails,
    ServicegroupName,
    ServiceName,
    ServiceState,
    SNMPDetectBaseType,
    state_markers,
    TimeRange,
    Timestamp,
)
from .host import HostAddress, HostgroupName, HostName, HostState
from .mrpe_config import ensure_mrpe_configs, MrpeConfig, MrpeConfigDeprecated
from .pluginname import ParsedSectionName, RuleSetName, SectionName, ValidatedString
from .protocol import Deserializer, Serializer
from .user_id import UserId
