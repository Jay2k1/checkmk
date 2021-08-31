#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from typing import Optional

import pytest

from cmk.base.plugins.agent_based.agent_based_api.v1.type_defs import StringTable
from cmk.base.plugins.agent_based.utils.cpu import ProcessorType
from cmk.base.plugins.agent_based.wmi_cpuload import parse_wmi_cpuload, Section


@pytest.mark.parametrize(
    "string_table, section",
    [
        pytest.param(
            [
                ["[system_perf]"],
                [
                    "AlignmentFixupsPersec", "Caption", "ContextSwitchesPersec", "Description",
                    "ExceptionDispatchesPersec", "FileControlBytesPersec",
                    "FileControlOperationsPersec", "FileDataOperationsPersec",
                    "FileReadBytesPersec", "FileReadOperationsPersec", "FileWriteBytesPersec",
                    "FileWriteOperationsPersec", "FloatingEmulationsPersec", "Frequency_Object",
                    "Frequency_PerfTime", "Frequency_Sys100NS", "Name", "PercentRegistryQuotaInUse",
                    "PercentRegistryQuotaInUse_Base", "Processes", "ProcessorQueueLength",
                    "SystemCallsPersec", "SystemUpTime", "Threads", "Timestamp_Object",
                    "Timestamp_PerfTime", "Timestamp_Sys100NS"
                ],
                [
                    "0", "", "-69479562", "", "14178685", "804099358366", "-783070306",
                    "1533491993", "154737860718293", "422989950", "3094169943814", "1110502043",
                    "0", "10000000", "2734511", "10000000", "", "152069756", "2147483647", "132",
                    "0", "-655373265", "131051948225967966", "2964", "131096941722079880",
                    "12303331974804", "131097013722070000"
                ],
                ["[computer_system]"],
                [
                    "AdminPasswordStatus", "AutomaticManagedPagefile", "AutomaticResetBootOption",
                    "AutomaticResetCapability", "BootOptionOnLimit", "BootOptionOnWatchDog",
                    "BootROMSupported", "BootupState", "Caption", "ChassisBootupState",
                    "CreationClassName", "CurrentTimeZone", "DaylightInEffect", "Description",
                    "DNSHostName", "Domain", "DomainRole", "EnableDaylightSavingsTime",
                    "FrontPanelResetStatus", "InfraredSupported", "InitialLoadInfo", "InstallDate",
                    "KeyboardPasswordStatus", "LastLoadInfo", "Manufacturer", "Model", "Name",
                    "NameFormat", "NetworkServerModeEnabled", "NumberOfLogicalProcessors",
                    "NumberOfProcessors", "OEMLogoBitmap", "OEMStringArray", "PartOfDomain",
                    "PauseAfterReset", "PCSystemType", "PowerManagementCapabilities",
                    "PowerManagementSupported", "PowerOnPasswordStatus", "PowerState",
                    "PowerSupplyState", "PrimaryOwnerContact", "PrimaryOwnerName",
                    "ResetCapability", "ResetCount", "ResetLimit", "Roles", "Status",
                    "SupportContactDescription", "SystemStartupDelay", "SystemStartupOptions",
                    "SystemStartupSetting", "SystemType", "ThermalState", "TotalPhysicalMemory",
                    "UserName", "WakeUpType", "Workgroup"
                ],
                [
                    "3", "0", "1", "1", "", "", "1", "Normal boot", "ROZRHPDB09", "3",
                    "Win32_ComputerSystem", "120", "1", "AT/AT COMPATIBLE", "ROZRHPDB09",
                    "testch.testint.net", "3", "1", "3", "0", "", "", "3", "", "HP",
                    "ProLiant DL380 G6", "ROZRHPDB09", "", "1", "16", "2", "", "<array>", "1", "-1",
                    "0", "", "", "3", "0", "3", "", "test International", "1", "-1", "-1",
                    "<array>", "OK", "", "", "", "", "x64-based PC", "3", "77298651136", "", "6", ""
                ],
            ],
            Section(
                load=0,
                timestamp=4499280.483715004,
                processor_type=ProcessorType.logical,
                n_cores=16,
            ),
            id="standard case 1",
        ),
        pytest.param(
            [
                ["[system_perf]"],
                [
                    "AlignmentFixupsPersec", "Caption", "ContextSwitchesPersec", "Description",
                    "ExceptionDispatchesPersec", "FileControlBytesPersec",
                    "FileControlOperationsPersec", "FileDataOperationsPersec",
                    "FileReadBytesPersec", "FileReadOperationsPersec", "FileWriteBytesPersec",
                    "FileWriteOperationsPersec", "FloatingEmulationsPersec", "Frequency_Object",
                    "Frequency_PerfTime", "Frequency_Sys100NS", "Name", "PercentRegistryQuotaInUse",
                    "PercentRegistryQuotaInUse_Base", "Processes", "ProcessorQueueLength",
                    "SystemCallsPersec", "SystemUpTime", "Threads", "Timestamp_Object",
                    "Timestamp_PerfTime", "Timestamp_Sys100NS"
                ],
                [
                    "0", "", "469922985", "", "222849", "6503221217", "72494625", "75272330",
                    "111617810637", "68676492", "34750951332", "6595838", "0", "10000000",
                    "2156247", "10000000", "", "250803278", "-1", "384", "0", "2144858950",
                    "131983188065000000", "5534", "131983336220258827", "31947393930",
                    "131983372220250000"
                ],
                ["[computer_system]"],
                [
                    "AdminPasswordStatus", "AutomaticManagedPagefile", "AutomaticResetBootOption",
                    "AutomaticResetCapability", "BootOptionOnLimit", "BootOptionOnWatchDog",
                    "BootROMSupported", "BootStatus", "BootupState", "Caption",
                    "ChassisBootupState", "ChassisSKUNumber", "CreationClassName",
                    "CurrentTimeZone", "DaylightInEffect", "Description", "DNSHostName", "Domain",
                    "DomainRole", "EnableDaylightSavingsTime", "FrontPanelResetStatus",
                    "HypervisorPresent", "InfraredSupported", "InitialLoadInfo", "InstallDate",
                    "KeyboardPasswordStatus", "LastLoadInfo", "Manufacturer", "Model", "Name",
                    "NameFormat", "NetworkServerModeEnabled", "NumberOfLogicalProcessors",
                    "NumberOfProcessors", "OEMLogoBitmap", "OEMStringArray", "PartOfDomain",
                    "PauseAfterReset", "PCSystemType", "PCSystemTypeEx",
                    "PowerManagementCapabilities", "PowerManagementSupported",
                    "PowerOnPasswordStatus", "PowerState", "PowerSupplyState",
                    "PrimaryOwnerContact", "PrimaryOwnerName", "ResetCapability", "ResetCount",
                    "ResetLimit", "Roles", "Status", "SupportContactDescription", "SystemFamily",
                    "SystemSKUNumber", "SystemStartupDelay", "SystemStartupOptions",
                    "SystemStartupSetting", "SystemType", "ThermalState", "TotalPhysicalMemory",
                    "UserName", "WakeUpType", "Workgroup"
                ],
                [
                    "3", "1", "1", "1", "", "", "1", "<array>", "Normal boot", "SERG-DELL", "3",
                    "Notebook", "Win32_ComputerSystem", "60", "0", "AT/AT COMPATIBLE", "SERG-DELL",
                    "WORKGROUP", "0", "1", "3", "0", "0", "", "", "3", "", "Dell Inc.",
                    "XPS 15 9570", "SERG-DELL", "", "1", "12", "1", "", "<array>", "0", "-1", "2",
                    "2", "", "", "3", "0", "3", "", "sk", "1", "-1", "-1", "<array>", "OK", "",
                    "XPS", "087C", "", "", "", "x64-based PC", "3", "34077048832", "SERG-DELL\\sk",
                    "6", "WORKGROUP"
                ],
            ],
            Section(
                load=0,
                timestamp=14816.203306021991,
                processor_type=ProcessorType.logical,
                n_cores=12,
            ),
            id="standard case 2",
        ),
        pytest.param(
            [
                ["[system_perf]"],
                [
                    "AlignmentFixupsPersec", "Caption", "ContextSwitchesPersec", "Description",
                    "ExceptionDispatchesPersec", "FileControlBytesPersec",
                    "FileControlOperationsPersec", "FileDataOperationsPersec",
                    "FileReadBytesPersec", "FileReadOperationsPersec", "FileWriteBytesPersec",
                    "FileWriteOperationsPersec", "FloatingEmulationsPersec", "Frequency_Object",
                    "Frequency_PerfTime", "Frequency_Sys100NS", "Name", "PercentRegistryQuotaInUse",
                    "PercentRegistryQuotaInUse_Base", "Processes", "ProcessorQueueLength",
                    "SystemCallsPersec", "SystemUpTime", "Threads", "Timestamp_Object",
                    "Timestamp_PerfTime", "Timestamp_Sys100NS", "WMIStatus"
                ],
                [
                    "0", "", "469922985", "", "222849", "6503221217", "72494625", "75272330",
                    "111617810637", "68676492", "34750951332", "6595838", "0", "10000000",
                    "2156247", "10000000", "", "250803278", "-1", "384", "0", "2144858950",
                    "131983188065000000", "5534", "131983336220258827", "31947393930",
                    "131983372220250000", "OK"
                ],
                ["[computer_system]"],
                [
                    "AdminPasswordStatus", "AutomaticManagedPagefile", "AutomaticResetBootOption",
                    "AutomaticResetCapability", "BootOptionOnLimit", "BootOptionOnWatchDog",
                    "BootROMSupported", "BootStatus", "BootupState", "Caption",
                    "ChassisBootupState", "ChassisSKUNumber", "CreationClassName",
                    "CurrentTimeZone", "DaylightInEffect", "Description", "DNSHostName", "Domain",
                    "DomainRole", "EnableDaylightSavingsTime", "FrontPanelResetStatus",
                    "HypervisorPresent", "InfraredSupported", "InitialLoadInfo", "InstallDate",
                    "KeyboardPasswordStatus", "LastLoadInfo", "Manufacturer", "Model", "Name",
                    "NameFormat", "NetworkServerModeEnabled", "NumberOfLogicalProcessors",
                    "NumberOfProcessors", "OEMLogoBitmap", "OEMStringArray", "PartOfDomain",
                    "PauseAfterReset", "PCSystemType", "PCSystemTypeEx",
                    "PowerManagementCapabilities", "PowerManagementSupported",
                    "PowerOnPasswordStatus", "PowerState", "PowerSupplyState",
                    "PrimaryOwnerContact", "PrimaryOwnerName", "ResetCapability", "ResetCount",
                    "ResetLimit", "Roles", "Status", "SupportContactDescription", "SystemFamily",
                    "SystemSKUNumber", "SystemStartupDelay", "SystemStartupOptions",
                    "SystemStartupSetting", "SystemType", "ThermalState", "TotalPhysicalMemory",
                    "UserName", "WakeUpType", "Workgroup", "WMIStatus"
                ],
                [
                    "3", "1", "1", "1", "", "", "1", "<array>", "Normal boot", "SERG-DELL", "3",
                    "Notebook", "Win32_ComputerSystem", "60", "0", "AT/AT COMPATIBLE", "SERG-DELL",
                    "WORKGROUP", "0", "1", "3", "0", "0", "", "", "3", "", "Dell Inc.",
                    "XPS 15 9570", "SERG-DELL", "", "1", "12", "1", "", "<array>", "0", "-1", "2",
                    "2", "", "", "3", "0", "3", "", "sk", "1", "-1", "-1", "<array>", "OK", "",
                    "XPS", "087C", "", "", "", "x64-based PC", "3", "34077048832", "SERG-DELL\\sk",
                    "6", "WORKGROUP", "OK"
                ],
            ],
            Section(
                load=0,
                timestamp=14816.203306021991,
                processor_type=ProcessorType.logical,
                n_cores=12,
            ),
            id="standard case 3",
        ),
        pytest.param(
            [
                ["[system_perf]"],
                [
                    "AlignmentFixupsPersec", "Caption", "ContextSwitchesPersec", "Description",
                    "ExceptionDispatchesPersec", "FileControlBytesPersec",
                    "FileControlOperationsPersec", "FileDataOperationsPersec",
                    "FileReadBytesPersec", "FileReadOperationsPersec", "FileWriteBytesPersec",
                    "FileWriteOperationsPersec", "FloatingEmulationsPersec", "Frequency_Object",
                    "Frequency_PerfTime", "Frequency_Sys100NS", "Name", "PercentRegistryQuotaInUse",
                    "PercentRegistryQuotaInUse_Base", "Processes", "ProcessorQueueLength",
                    "SystemCallsPersec", "SystemUpTime", "Threads", "Timestamp_Object",
                    "Timestamp_PerfTime", "Timestamp_Sys100NS", "WMIStatus"
                ],
                [
                    "0", "", "469922985", "", "222849", "6503221217", "72494625", "75272330",
                    "111617810637", "68676492", "34750951332", "6595838", "0", "10000000",
                    "2156247", "10000000", "", "250803278", "-1", "384", "0", "2144858950",
                    "131983188065000000", "5534", "131983336220258827", "31947393930",
                    "131983372220250000", "Timeout"
                ],
                ["[computer_system]"],
                [
                    "AdminPasswordStatus", "AutomaticManagedPagefile", "AutomaticResetBootOption",
                    "AutomaticResetCapability", "BootOptionOnLimit", "BootOptionOnWatchDog",
                    "BootROMSupported", "BootStatus", "BootupState", "Caption",
                    "ChassisBootupState", "ChassisSKUNumber", "CreationClassName",
                    "CurrentTimeZone", "DaylightInEffect", "Description", "DNSHostName", "Domain",
                    "DomainRole", "EnableDaylightSavingsTime", "FrontPanelResetStatus",
                    "HypervisorPresent", "InfraredSupported", "InitialLoadInfo", "InstallDate",
                    "KeyboardPasswordStatus", "LastLoadInfo", "Manufacturer", "Model", "Name",
                    "NameFormat", "NetworkServerModeEnabled", "NumberOfLogicalProcessors",
                    "NumberOfProcessors", "OEMLogoBitmap", "OEMStringArray", "PartOfDomain",
                    "PauseAfterReset", "PCSystemType", "PCSystemTypeEx",
                    "PowerManagementCapabilities", "PowerManagementSupported",
                    "PowerOnPasswordStatus", "PowerState", "PowerSupplyState",
                    "PrimaryOwnerContact", "PrimaryOwnerName", "ResetCapability", "ResetCount",
                    "ResetLimit", "Roles", "Status", "SupportContactDescription", "SystemFamily",
                    "SystemSKUNumber", "SystemStartupDelay", "SystemStartupOptions",
                    "SystemStartupSetting", "SystemType", "ThermalState", "TotalPhysicalMemory",
                    "UserName", "WakeUpType", "Workgroup", "WMIStatus"
                ],
                [
                    "3", "1", "1", "1", "", "", "1", "<array>", "Normal boot", "SERG-DELL", "3",
                    "Notebook", "Win32_ComputerSystem", "60", "0", "AT/AT COMPATIBLE", "SERG-DELL",
                    "WORKGROUP", "0", "1", "3", "0", "0", "", "", "3", "", "Dell Inc.",
                    "XPS 15 9570", "SERG-DELL", "", "1", "12", "1", "", "<array>", "0", "-1", "2",
                    "2", "", "", "3", "0", "3", "", "sk", "1", "-1", "-1", "<array>", "OK", "",
                    "XPS", "087C", "", "", "", "x64-based PC", "3", "34077048832", "SERG-DELL\\sk",
                    "6", "WORKGROUP", "OK"
                ],
            ],
            None,
            id="wmi timeout 1",
        ),
        pytest.param(
            [
                ["[system_perf]"],
                [
                    "AlignmentFixupsPersec", "Caption", "ContextSwitchesPersec", "Description",
                    "ExceptionDispatchesPersec", "FileControlBytesPersec",
                    "FileControlOperationsPersec", "FileDataOperationsPersec",
                    "FileReadBytesPersec", "FileReadOperationsPersec", "FileWriteBytesPersec",
                    "FileWriteOperationsPersec", "FloatingEmulationsPersec", "Frequency_Object",
                    "Frequency_PerfTime", "Frequency_Sys100NS", "Name", "PercentRegistryQuotaInUse",
                    "PercentRegistryQuotaInUse_Base", "Processes", "ProcessorQueueLength",
                    "SystemCallsPersec", "SystemUpTime", "Threads", "Timestamp_Object",
                    "Timestamp_PerfTime", "Timestamp_Sys100NS", "WMIStatus"
                ],
                [
                    "0", "", "469922985", "", "222849", "6503221217", "72494625", "75272330",
                    "111617810637", "68676492", "34750951332", "6595838", "0", "10000000",
                    "2156247", "10000000", "", "250803278", "-1", "384", "0", "2144858950",
                    "131983188065000000", "5534", "131983336220258827", "31947393930",
                    "131983372220250000", "OK"
                ],
                ["[computer_system]"],
                [
                    "AdminPasswordStatus", "AutomaticManagedPagefile", "AutomaticResetBootOption",
                    "AutomaticResetCapability", "BootOptionOnLimit", "BootOptionOnWatchDog",
                    "BootROMSupported", "BootStatus", "BootupState", "Caption",
                    "ChassisBootupState", "ChassisSKUNumber", "CreationClassName",
                    "CurrentTimeZone", "DaylightInEffect", "Description", "DNSHostName", "Domain",
                    "DomainRole", "EnableDaylightSavingsTime", "FrontPanelResetStatus",
                    "HypervisorPresent", "InfraredSupported", "InitialLoadInfo", "InstallDate",
                    "KeyboardPasswordStatus", "LastLoadInfo", "Manufacturer", "Model", "Name",
                    "NameFormat", "NetworkServerModeEnabled", "NumberOfLogicalProcessors",
                    "NumberOfProcessors", "OEMLogoBitmap", "OEMStringArray", "PartOfDomain",
                    "PauseAfterReset", "PCSystemType", "PCSystemTypeEx",
                    "PowerManagementCapabilities", "PowerManagementSupported",
                    "PowerOnPasswordStatus", "PowerState", "PowerSupplyState",
                    "PrimaryOwnerContact", "PrimaryOwnerName", "ResetCapability", "ResetCount",
                    "ResetLimit", "Roles", "Status", "SupportContactDescription", "SystemFamily",
                    "SystemSKUNumber", "SystemStartupDelay", "SystemStartupOptions",
                    "SystemStartupSetting", "SystemType", "ThermalState", "TotalPhysicalMemory",
                    "UserName", "WakeUpType", "Workgroup", "WMIStatus"
                ],
                [
                    "3", "1", "1", "1", "", "", "1", "<array>", "Normal boot", "SERG-DELL", "3",
                    "Notebook", "Win32_ComputerSystem", "60", "0", "AT/AT COMPATIBLE", "SERG-DELL",
                    "WORKGROUP", "0", "1", "3", "0", "0", "", "", "3", "", "Dell Inc.",
                    "XPS 15 9570", "SERG-DELL", "", "1", "12", "1", "", "<array>", "0", "-1", "2",
                    "2", "", "", "3", "0", "3", "", "sk", "1", "-1", "-1", "<array>", "OK", "",
                    "XPS", "087C", "", "", "", "x64-based PC", "3", "34077048832", "SERG-DELL\\sk",
                    "6", "WORKGROUP", "Timeout"
                ],
            ],
            None,
            id="wmi timeout 2",
        ),
        pytest.param(
            [
                ["[system_perf]"],
                [
                    "AlignmentFixupsPersec", "Caption", "ContextSwitchesPersec", "Description",
                    "ExceptionDispatchesPersec", "FileControlBytesPersec",
                    "FileControlOperationsPersec", "FileDataOperationsPersec",
                    "FileReadBytesPersec", "FileReadOperationsPersec", "FileWriteBytesPersec",
                    "FileWriteOperationsPersec", "FloatingEmulationsPersec", "Frequency_Object",
                    "Frequency_PerfTime", "Frequency_Sys100NS", "Name", "PercentRegistryQuotaInUse",
                    "PercentRegistryQuotaInUse_Base", "Processes", "ProcessorQueueLength",
                    "SystemCallsPersec", "SystemUpTime", "Threads", "Timestamp_Object",
                    "Timestamp_PerfTime", "Timestamp_Sys100NS", "WMIStatus"
                ],
                [
                    "0", "", "469922985", "", "222849", "6503221217", "72494625", "75272330",
                    "111617810637", "68676492", "34750951332", "6595838", "0", "10000000",
                    "2156247", "10000000", "", "250803278", "-1", "384", "0", "2144858950",
                    "131983188065000000", "5534", "131983336220258827", "31947393930",
                    "131983372220250000", "Timeout"
                ],
                ["[computer_system]"],
                [
                    "AdminPasswordStatus", "AutomaticManagedPagefile", "AutomaticResetBootOption",
                    "AutomaticResetCapability", "BootOptionOnLimit", "BootOptionOnWatchDog",
                    "BootROMSupported", "BootStatus", "BootupState", "Caption",
                    "ChassisBootupState", "ChassisSKUNumber", "CreationClassName",
                    "CurrentTimeZone", "DaylightInEffect", "Description", "DNSHostName", "Domain",
                    "DomainRole", "EnableDaylightSavingsTime", "FrontPanelResetStatus",
                    "HypervisorPresent", "InfraredSupported", "InitialLoadInfo", "InstallDate",
                    "KeyboardPasswordStatus", "LastLoadInfo", "Manufacturer", "Model", "Name",
                    "NameFormat", "NetworkServerModeEnabled", "NumberOfLogicalProcessors",
                    "NumberOfProcessors", "OEMLogoBitmap", "OEMStringArray", "PartOfDomain",
                    "PauseAfterReset", "PCSystemType", "PCSystemTypeEx",
                    "PowerManagementCapabilities", "PowerManagementSupported",
                    "PowerOnPasswordStatus", "PowerState", "PowerSupplyState",
                    "PrimaryOwnerContact", "PrimaryOwnerName", "ResetCapability", "ResetCount",
                    "ResetLimit", "Roles", "Status", "SupportContactDescription", "SystemFamily",
                    "SystemSKUNumber", "SystemStartupDelay", "SystemStartupOptions",
                    "SystemStartupSetting", "SystemType", "ThermalState", "TotalPhysicalMemory",
                    "UserName", "WakeUpType", "Workgroup", "WMIStatus"
                ],
                [
                    "3", "1", "1", "1", "", "", "1", "<array>", "Normal boot", "SERG-DELL", "3",
                    "Notebook", "Win32_ComputerSystem", "60", "0", "AT/AT COMPATIBLE", "SERG-DELL",
                    "WORKGROUP", "0", "1", "3", "0", "0", "", "", "3", "", "Dell Inc.",
                    "XPS 15 9570", "SERG-DELL", "", "1", "12", "1", "", "<array>", "0", "-1", "2",
                    "2", "", "", "3", "0", "3", "", "sk", "1", "-1", "-1", "<array>", "OK", "",
                    "XPS", "087C", "", "", "", "x64-based PC", "3", "34077048832", "SERG-DELL\\sk",
                    "6", "WORKGROUP", "Timeout"
                ],
            ],
            None,
            id="wmi timeout 3",
        ),
        pytest.param(
            [
                ["[system_perf]"],
                ["WMItimeout"],
                ["[computer_system]"],
                [
                    "AdminPasswordStatus", "AutomaticManagedPagefile", "AutomaticResetBootOption",
                    "AutomaticResetCapability", "BootOptionOnLimit", "BootOptionOnWatchDog",
                    "BootROMSupported", "BootStatus", "BootupState", "Caption",
                    "ChassisBootupState", "ChassisSKUNumber", "CreationClassName",
                    "CurrentTimeZone", "DaylightInEffect", "Description", "DNSHostName", "Domain",
                    "DomainRole", "EnableDaylightSavingsTime", "FrontPanelResetStatus",
                    "HypervisorPresent", "InfraredSupported", "InitialLoadInfo", "InstallDate",
                    "KeyboardPasswordStatus", "LastLoadInfo", "Manufacturer", "Model", "Name",
                    "NameFormat", "NetworkServerModeEnabled", "NumberOfLogicalProcessors",
                    "NumberOfProcessors", "OEMLogoBitmap", "OEMStringArray", "PartOfDomain",
                    "PauseAfterReset", "PCSystemType", "PCSystemTypeEx",
                    "PowerManagementCapabilities", "PowerManagementSupported",
                    "PowerOnPasswordStatus", "PowerState", "PowerSupplyState",
                    "PrimaryOwnerContact", "PrimaryOwnerName", "ResetCapability", "ResetCount",
                    "ResetLimit", "Roles", "Status", "SupportContactDescription", "SystemFamily",
                    "SystemSKUNumber", "SystemStartupDelay", "SystemStartupOptions",
                    "SystemStartupSetting", "SystemType", "ThermalState", "TotalPhysicalMemory",
                    "UserName", "WakeUpType", "Workgroup"
                ],
                [
                    "3", "1", "1", "1", "", "", "1", "<array>", "Normal boot", "SERG-DELL", "3",
                    "Notebook", "Win32_ComputerSystem", "60", "0", "AT/AT COMPATIBLE", "SERG-DELL",
                    "WORKGROUP", "0", "1", "3", "0", "0", "", "", "3", "", "Dell Inc.",
                    "XPS 15 9570", "SERG-DELL", "", "1", "12", "1", "", "<array>", "0", "-1", "2",
                    "2", "", "", "3", "0", "3", "", "sk", "1", "-1", "-1", "<array>", "OK", "",
                    "XPS", "087C", "", "", "", "x64-based PC", "3", "34077048832", "SERG-DELL\\sk",
                    "6", "WORKGROUP"
                ],
            ],
            None,
            id="wmi timeout 4",
        ),
        pytest.param(
            [
                ["[system_perf]"],
                [
                    "AlignmentFixupsPersec", "Caption", "ContextSwitchesPersec", "Description",
                    "ExceptionDispatchesPersec", "FileControlBytesPersec",
                    "FileControlOperationsPersec", "FileDataOperationsPersec",
                    "FileReadBytesPersec", "FileReadOperationsPersec", "FileWriteBytesPersec",
                    "FileWriteOperationsPersec", "FloatingEmulationsPersec", "Frequency_Object",
                    "Frequency_PerfTime", "Frequency_Sys100NS", "Name", "PercentRegistryQuotaInUse",
                    "PercentRegistryQuotaInUse_Base", "Processes", "ProcessorQueueLength",
                    "SystemCallsPersec", "SystemUpTime", "Threads", "Timestamp_Object",
                    "Timestamp_PerfTime", "Timestamp_Sys100NS"
                ],
                [
                    "0", "", "469922985", "", "222849", "6503221217", "72494625", "75272330",
                    "111617810637", "68676492", "34750951332", "6595838", "0", "10000000",
                    "2156247", "10000000", "", "250803278", "-1", "384", "0", "2144858950",
                    "131983188065000000", "5534", "131983336220258827", "31947393930",
                    "131983372220250000"
                ],
                ["[computer_system]"],
                ["WMItimeout"],
            ],
            None,
            id="wmi timeout 5",
        ),
        pytest.param(
            [
                ["[system_perf]"],
                ["WMItimeout"],
                ["[computer_system]"],
                ["WMItimeout"],
            ],
            None,
            id="wmi timeout 6",
        ),
        pytest.param(
            [
                ["[system_perf]"],
                [
                    "AlignmentFixupsPersec", "Caption", "ContextSwitchesPersec", "Description",
                    "ExceptionDispatchesPersec", "FileControlBytesPersec",
                    "FileControlOperationsPersec", "FileDataOperationsPersec",
                    "FileReadBytesPersec", "FileReadOperationsPersec", "FileWriteBytesPersec",
                    "FileWriteOperationsPersec", "FloatingEmulationsPersec", "Frequency_Object",
                    "Frequency_PerfTime", "Frequency_Sys100NS", "Name", "PercentRegistryQuotaInUse",
                    "PercentRegistryQuotaInUse_Base", "Processes", "ProcessorQueueLength",
                    "SystemCallsPersec", "SystemUpTime", "Threads", "Timestamp_Object",
                    "Timestamp_PerfTime", "Timestamp_Sys100NS"
                ],
                [
                    "0", "", "515871527", "", "80813", "1740164809", "35749693", "19282359",
                    "71868764935", "17418626", "10976290970", "1863733", "0", "10000000", "1757890",
                    "10000000", "", "50230448", "714429781", "59", "0", "-1438646331",
                    "131087385121255994", "762", "131090689667831652", "580911371748",
                    "131090761667830000"
                ],
            ],
            None,
            id="computer_system table missing",
        ),
    ],
)
def test_parse_wmi_cpuload(
    string_table: StringTable,
    section: Optional[Section],
) -> None:
    assert parse_wmi_cpuload(string_table) == section
