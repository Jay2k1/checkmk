#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from cmk.gui import utils
from cmk.gui.type_defs import Users, UserSpec

from ._check_credentials import (
    check_credentials,
    create_non_existing_user,
    is_customer_user_allowed_to_login,
    user_exists,
    user_exists_according_to_profile,
    user_locked,
)
from ._connections import (
    active_connections,
    active_connections_by_type,
    ACTIVE_DIR,
    ActivePlugins,
    builtin_connections,
    clear_user_connection_cache,
    ConfigurableUserConnectionSpec,
    connection_choices,
    connections_by_type,
    CUSTOM_USER_ATTRIBUTE,
    DIR_SERVER_389,
    DISABLE_NOTIFICATIONS,
    DisableNotificationsAttribute,
    Discover,
    Fixed,
    FORCE_AUTH_USER,
    get_active_saml_connections,
    get_connection,
    get_ldap_connections,
    get_saml_connections,
    GroupsToAttributes,
    GroupsToContactGroups,
    GroupsToSync,
    HtpasswdUserConnectionConfig,
    ICONS_PER_ITEM,
    LDAPConnectionConfigDiscover,
    LDAPConnectionConfigFixed,
    LDAPUserConnectionConfig,
    load_connection_config,
    locked_attributes,
    multisite_attributes,
    NAV_HIDE_ICONS_TITLE,
    non_contact_attributes,
    OPEN_LDAP,
    register_config_file,
    SAMLUserConnectionConfig,
    save_connection_config,
    save_snapshot_user_connection_config,
    SHOW_MODE,
    START_URL,
    SyncAttribute,
    TEMP_UNIT,
    UI_SIDEBAR_POSITIONS,
    UI_THEME,
    UserConnectionConfigFile,
)
from ._connector import (
    CheckCredentialsResult,
    ConnectorType,
    user_connector_registry,
    UserConnectionConfig,
    UserConnector,
    UserConnectorRegistry,
)
from ._custom_attributes import update_config_based_user_attributes
from ._find_usage import find_timeperiod_usage_in_notification_rule
from ._need_to_change_pw import is_automation_user, need_to_change_pw
from ._on_failed_login import on_failed_login
from ._roles import load_roles, register_userroles_config_file, UserRole, UserRolesConfigFile
from ._two_factor import (
    disable_two_factor_authentication,
    is_two_factor_backup_code_valid,
    is_two_factor_login_enabled,
    load_two_factor_credentials,
    make_two_factor_backup_codes,
)
from ._user_attribute import (
    get_user_attributes,
    get_user_attributes_by_topic,
    user_attribute_registry,
    UserAttribute,
    UserAttributeRegistry,
)
from ._user_selection import UserSelection
from ._user_spec import add_internal_attributes, new_user_template, USER_SCHEME_SERIAL
from ._user_sync_config import user_sync_config, user_sync_default_config
from .session import is_valid_user_session, load_session_infos
from .store import (
    contactgroups_of_user,
    convert_idle_timeout,
    create_cmk_automation_user,
    custom_attr_path,
    general_userdb_job,
    get_last_activity,
    get_last_seen,
    get_online_user_ids,
    load_contacts,
    load_custom_attr,
    load_multisite_users,
    load_user,
    load_users,
    release_users_lock,
    remove_custom_attr,
    rewrite_users,
    save_custom_attr,
    save_two_factor_credentials,
    save_users,
    write_contacts_and_users_file,
)
from .user_attributes import show_mode_choices, validate_start_url

__all__ = [
    "active_connections",
    "active_connections_by_type",
    "add_internal_attributes",
    "ActivePlugins",
    "ACTIVE_DIR",
    "builtin_connections",
    "check_credentials",
    "clear_user_connection_cache",
    "connection_choices",
    "connections_by_type",
    "contactgroups_of_user",
    "convert_idle_timeout",
    "create_cmk_automation_user",
    "create_non_existing_user",
    "custom_attr_path",
    "CheckCredentialsResult",
    "ConnectorType",
    "CUSTOM_USER_ATTRIBUTE",
    "DisableNotificationsAttribute",
    "Discover",
    "DIR_SERVER_389",
    "DISABLE_NOTIFICATIONS",
    "user_sync_config",
    "user_sync_default_config",
    "disable_two_factor_authentication",
    "find_timeperiod_usage_in_notification_rule",
    "Fixed",
    "FORCE_AUTH_USER",
    "general_userdb_job",
    "get_active_saml_connections",
    "get_connection",
    "get_last_activity",
    "get_last_seen",
    "get_ldap_connections",
    "get_online_user_ids",
    "get_saml_connections",
    "get_user_attributes",
    "get_user_attributes_by_topic",
    "GroupsToAttributes",
    "GroupsToContactGroups",
    "GroupsToSync",
    "is_automation_user",
    "is_customer_user_allowed_to_login",
    "is_two_factor_backup_code_valid",
    "is_two_factor_login_enabled",
    "is_valid_user_session",
    "ICONS_PER_ITEM",
    "load_connection_config",
    "load_contacts",
    "load_custom_attr",
    "load_multisite_users",
    "load_roles",
    "load_session_infos",
    "load_two_factor_credentials",
    "load_user",
    "load_users",
    "locked_attributes",
    "LDAPConnectionConfigDiscover",
    "LDAPConnectionConfigFixed",
    "LDAPUserConnectionConfig",
    "make_two_factor_backup_codes",
    "multisite_attributes",
    "need_to_change_pw",
    "new_user_template",
    "non_contact_attributes",
    "NAV_HIDE_ICONS_TITLE",
    "on_failed_login",
    "OPEN_LDAP",
    "UserConnectionConfigFile",
    "register_config_file",
    "register_userroles_config_file",
    "release_users_lock",
    "remove_custom_attr",
    "rewrite_users",
    "save_connection_config",
    "save_custom_attr",
    "save_snapshot_user_connection_config",
    "save_two_factor_credentials",
    "save_users",
    "show_mode_choices",
    "SyncAttribute",
    "SHOW_MODE",
    "START_URL",
    "SAMLUserConnectionConfig",
    "HtpasswdUserConnectionConfig",
    "TEMP_UNIT",
    "update_config_based_user_attributes",
    "user_attribute_registry",
    "user_connector_registry",
    "user_exists",
    "user_exists_according_to_profile",
    "user_locked",
    "user_sync_config",
    "user_sync_default_config",
    "UserAttribute",
    "UserAttributeRegistry",
    "UserConnectionConfig",
    "ConfigurableUserConnectionSpec",
    "UserRole",
    "UserRolesConfigFile",
    "UserConnector",
    "UserConnectorRegistry",
    "UserSelection",
    "UserSpec",
    "Users",
    "UI_SIDEBAR_POSITIONS",
    "UI_THEME",
    "USER_SCHEME_SERIAL",
    "validate_start_url",
    "write_contacts_and_users_file",
]


def load_plugins() -> None:
    """Plugin initialization hook (Called by cmk.gui.main_modules.load_plugins())"""
    utils.load_web_plugins("userdb", globals())
