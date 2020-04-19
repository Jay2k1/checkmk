#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import socket
import shutil
import sys
# Explicitly check for Python 3 (which is understood by mypy)
if sys.version_info[0] >= 3:
    from pathlib import Path  # pylint: disable=import-error
else:
    from pathlib2 import Path  # pylint: disable=import-error
import pytest  # type: ignore[import]

import cmk.utils.paths
import cmk.utils.store as store
import cmk.utils.version as cmk_version


@pytest.fixture(autouse=True, scope="function")
def patch_omd_site(monkeypatch):
    monkeypatch.setenv("OMD_SITE", "NO_SITE")
    monkeypatch.setattr(cmk_version, "omd_site", lambda: "NO_SITE")

    _touch(cmk.utils.paths.htpasswd_file)
    store.makedirs(cmk.utils.paths.var_dir + '/web')
    store.makedirs(cmk.utils.paths.var_dir + '/php-api')
    store.makedirs(cmk.utils.paths.var_dir + '/wato/php-api')
    store.makedirs(cmk.utils.paths.var_dir + "/wato/auth")
    store.makedirs(cmk.utils.paths.omd_root + '/var/log')
    store.makedirs(cmk.utils.paths.omd_root + '/tmp/check_mk')


def _touch(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).touch()


@pytest.fixture(autouse=True, scope="function")
def cleanup_after_test():
    yield

    # Ensure there is no file left over in the unit test fake site
    # to prevent tests involving eachother
    for entry in Path(cmk.utils.paths.omd_root).iterdir():
        if entry.is_dir():
            shutil.rmtree(str(entry))
        else:
            entry.unlink()


# Unit tests should not be executed in site.
# -> Disabled site fixture for them
@pytest.fixture(scope="session")
def site(request):
    pass


# TODO: This fixes our unit tests when executing the tests while the local
# resolver uses a search domain which uses wildcard resolution. e.g. in a
# network where mathias-kettner.de is in the domain search list and
# [anything].mathias-kettner.de resolves to an IP address.
# Clean this up once we don't have this situation anymore e.g. via VPN.
@pytest.fixture()
def fixup_ip_lookup(monkeypatch):
    # Fix IP lookup when
    def _getaddrinfo(host, port, family=None, socktype=None, proto=None, flags=None):
        if family == socket.AF_INET:
            # TODO: This is broken. It should return (family, type, proto, canonname, sockaddr)
            return "0.0.0.0"
        raise NotImplementedError()

    monkeypatch.setattr(socket, "getaddrinfo", _getaddrinfo)
