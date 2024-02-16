#!/usr/bin/env python3
# Copyright (C) 2023 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from cmk.rulesets.v1 import form_specs, Localizable, rule_specs, validators
from cmk.rulesets.v1.migrations import migrate_to_upper_float_levels


def fs_mssql_backup_age(
    title: Localizable,
) -> form_specs.DictElement[form_specs.LevelsConfigModel[float]]:
    return form_specs.DictElement[form_specs.LevelsConfigModel[float]](
        parameter_form=form_specs.Levels[float](
            title=title,
            level_direction=form_specs.LevelDirection.UPPER,
            form_spec_template=form_specs.TimeSpan(
                displayed_magnitudes=tuple(form_specs.TimeMagnitude)
            ),
            predictive=None,
            migrate=migrate_to_upper_float_levels,
            prefill_fixed_levels=form_specs.InputHint(value=(0.0, 0.0)),
        )
    )


def mssql_condition_instance_tablespace() -> rule_specs.HostAndItemCondition:
    return rule_specs.HostAndItemCondition(
        item_title=Localizable("Instance & tablespace name"),
        item_form=form_specs.Text(
            help_text=Localizable(
                "The MSSQL instance name and the tablespace name separated by a space."
            ),
            custom_validate=validators.DisallowEmpty(),
        ),
    )
