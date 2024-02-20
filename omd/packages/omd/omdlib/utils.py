#!/usr/bin/env python3
# Copyright (C) 2023 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import contextlib
import enum
import os
import pwd
import shutil
from collections.abc import Iterator
from pathlib import Path

from omdlib.skel_permissions import get_skel_permissions, Permissions
from omdlib.type_defs import Replacements


def is_containerized() -> bool:
    return (
        os.path.exists("/.dockerenv")
        or os.path.exists("/run/.containerenv")
        or os.environ.get("CMK_CONTAINERIZED") == "TRUE"
    )


@contextlib.contextmanager
def chdir(path: str) -> Iterator[None]:
    """Change working directory and return on exit"""
    prev_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def delete_user_file(user_path: str) -> None:
    if not os.path.islink(user_path) and os.path.isdir(user_path):
        shutil.rmtree(user_path)
    else:
        os.remove(user_path)


def delete_directory_contents(d: str) -> None:
    for f in os.listdir(d):
        delete_user_file(d + "/" + f)


def omd_base_path() -> str:
    return "/"


def get_editor() -> str:
    alternative = os.environ.get("EDITOR", "/usr/bin/vi")
    editor = os.environ.get("VISUAL", alternative)

    if not os.path.exists(editor):
        return "vi"

    return editor


def chown_tree(directory: str, user: str) -> None:
    uid = pwd.getpwnam(user).pw_uid
    gid = pwd.getpwnam(user).pw_gid
    os.chown(directory, uid, gid)
    for dirpath, dirnames, filenames in os.walk(directory):
        for entry in dirnames + filenames:
            os.lchown(dirpath + "/" + entry, uid, gid)


def create_skeleton_file(
    skelbase: str,
    userbase: str,
    relpath: str,
    replacements: Replacements,
    permissions: Permissions,
) -> None:
    skel_path = Path(skelbase, relpath)
    user_path = Path(userbase, relpath)

    # Remove old version, if existing (needed during update)
    if user_path.exists():
        delete_user_file(str(user_path))

    # Create directories, symlinks and files
    if skel_path.is_symlink():
        user_path.symlink_to(skel_path.readlink())
    elif skel_path.is_dir():
        user_path.mkdir(parents=True)
    else:
        user_path.write_bytes(replace_tags(skel_path.read_bytes(), replacements))

    if not skel_path.is_symlink():
        user_path.chmod(get_skel_permissions(skelbase, permissions, relpath.removeprefix("./")))


def create_skeleton_files(
    site_dir: str,
    replacements: Replacements,
    skelroot: str,
    skel_permissions: Permissions,
    directory: str,
) -> None:
    # Hack: exclude tmp if dir is '.'
    exclude_tmp = directory == "."
    with chdir(skelroot):  # make relative paths
        for dirpath, dirnames, filenames in os.walk(directory):
            dirpath = dirpath.removeprefix("./")
            for entry in dirnames + filenames:
                if exclude_tmp:
                    if dirpath == "." and entry == "tmp":
                        continue
                    if dirpath == "tmp" or dirpath.startswith("tmp/"):
                        continue
                create_skeleton_file(
                    skelroot, site_dir, dirpath + "/" + entry, replacements, skel_permissions
                )


def replace_tags(content: bytes, replacements: Replacements) -> bytes:
    for var, value in replacements.items():
        content = content.replace(var.encode("utf-8"), value.encode("utf-8"))
    return content


class SiteDistributedSetup(str, enum.Enum):
    DISTRIBUTED_REMOTE = "distributed_remote"
    NOT_DISTRIBUTED = "not_distributed"
    UNKNOWN = "unknown"


def get_site_distributed_setup() -> SiteDistributedSetup:
    file_vars: dict = {}
    if (distr_wato_filepath := Path("~/etc/omd/distributed.mk").expanduser()).exists():
        exec(  # nosec B102 # BNS:aee528
            distr_wato_filepath.read_text(),
            file_vars,
            file_vars,
        )
    if "is_wato_remote_site" not in file_vars:
        return SiteDistributedSetup.UNKNOWN
    if file_vars["is_wato_remote_site"] is True:
        return SiteDistributedSetup.DISTRIBUTED_REMOTE
    return SiteDistributedSetup.NOT_DISTRIBUTED
