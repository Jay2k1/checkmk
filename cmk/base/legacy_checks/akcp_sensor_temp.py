#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.


# Example for contents of info
#   description     degree  unit status low_crit low_warn high_warn  high_crit degreeraw online
# ["HGS-RZ1TEMP-TH1", "22", "1",   "2",   "18",   "20",    "25",      "28",      "",     "1"]


from cmk.base.check_api import LegacyCheckDefinition
from cmk.base.check_legacy_includes.akcp_sensor import (
    AKCP_TEMP_CHECK_DEFAULT_PARAMETERS,
    check_akcp_sensor_temp,
    inventory_akcp_sensor_temp,
)
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import all_of, not_exists, SNMPTree, startswith

check_info["akcp_sensor_temp"] = LegacyCheckDefinition(
    detect=all_of(
        startswith(".1.3.6.1.2.1.1.2.0", ".1.3.6.1.4.1.3854.1"), not_exists(".1.3.6.1.4.1.3854.2.*")
    ),
    check_function=check_akcp_sensor_temp,
    discovery_function=inventory_akcp_sensor_temp,
    service_name="Temperature %s",
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.3854.1.2.2.1.16.1",
        oids=["1", "3", "12", "4", "10", "9", "7", "8", "14", "5"],
    ),
    check_ruleset_name="temperature",
    check_default_parameters=AKCP_TEMP_CHECK_DEFAULT_PARAMETERS,
)
