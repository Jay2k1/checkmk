#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import logging
import multiprocessing
import sys
import threading
import time

import pytest

from tests.testlib.utils import wait_until

import cmk.utils.log
import cmk.utils.paths

import cmk.gui.log
from cmk.gui.background_job import (
    BackgroundJob,
    BackgroundJobAlreadyRunning,
    BackgroundJobDefines,
    BackgroundProcessInterface,
    InitialStatusArgs,
    job_registry,
    JobStatusStates,
    running_job_ids,
    wait_for_background_jobs,
)

import cmk.ccc.version as cmk_version


def test_registered_background_jobs() -> None:
    expected_jobs = [
        "ActivateChangesSchedulerBackgroundJob",
        "ParentScanBackgroundJob",
        "RenameHostsBackgroundJob",
        "RenameHostBackgroundJob",
        "FetchAgentOutputBackgroundJob",
        "OMDConfigChangeBackgroundJob",
        "BulkDiscoveryBackgroundJob",
        "UserSyncBackgroundJob",
        "UserProfileCleanupBackgroundJob",
        "ServiceDiscoveryBackgroundJob",
        "ActivationCleanupBackgroundJob",
        "CheckmkAutomationBackgroundJob",
        "DiagnosticsDumpBackgroundJob",
        "SearchIndexBackgroundJob",
        "SpecGeneratorBackgroundJob",
        "DiscoveredHostLabelSyncJob",
        "SyncRemoteSitesBackgroundJob",
        "HostRemovalBackgroundJob",
        "AutodiscoveryBackgroundJob",
    ]

    if cmk_version.edition(cmk.utils.paths.omd_root) is not cmk_version.Edition.CRE:
        expected_jobs += [
            "HostRegistrationBackgroundJob",
            "DiscoverRegisteredHostsBackgroundJob",
            "BakeAgentsBackgroundJob",
            "SignAgentsBackgroundJob",
            "ReportingBackgroundJob",
            "LicensingOnlineVerificationBackgroundJob",
        ]

    assert sorted(job_registry.keys()) == sorted(expected_jobs)


def test_registered_background_jobs_attributes() -> None:
    for job_class in job_registry.values():
        assert isinstance(job_class.job_prefix, str)
        assert isinstance(job_class.gui_title(), str)


@pytest.fixture(autouse=True)
def job_base_dir(tmp_path, monkeypatch):
    var_dir = tmp_path

    log_dir = var_dir / "log"
    log_dir.mkdir()

    job_dir = var_dir / "background_jobs"
    job_dir.mkdir()

    # Patch for web.log. Sholdn't we do this for all web tests?
    monkeypatch.setattr(cmk.utils.paths, "log_dir", str(log_dir))

    monkeypatch.setattr(BackgroundJobDefines, "base_dir", str(job_dir))
    return job_dir


class DummyBackgroundJob(BackgroundJob):
    job_prefix = "dummy_job"

    @classmethod
    def gui_title(cls) -> str:
        return "Dummy Job"

    def __init__(self) -> None:
        self.finish_hello_event = multiprocessing.get_context("spawn").Event()

        super().__init__(self.job_prefix)

    def execute_hello(self, job_interface: BackgroundProcessInterface) -> None:
        sys.stdout.write("Hallo :-)\n")
        sys.stdout.flush()
        self.finish_hello_event.wait()

    def execute_endless(self, job_interface: BackgroundProcessInterface) -> None:
        sys.stdout.write("Hanging loop\n")
        sys.stdout.flush()
        time.sleep(100)


@pytest.mark.skip(reason="Fails randomly: see CMK-18161")
def test_start_job() -> None:
    job = DummyBackgroundJob()

    status = job.get_status()
    assert status.state == JobStatusStates.INITIALIZED

    job.start(
        job.execute_hello,
        InitialStatusArgs(
            title=job.gui_title(),
            deletable=False,
            stoppable=True,
            user=None,
        ),
        override_job_log_level=logging.DEBUG,
    )
    wait_until(job.is_active, timeout=10, interval=0.1)

    with pytest.raises(BackgroundJobAlreadyRunning):
        job.start(
            job.execute_hello,
            InitialStatusArgs(
                title=job.gui_title(),
                deletable=False,
                stoppable=True,
                user=None,
            ),
        )
    assert job.is_active()

    job.finish_hello_event.set()

    wait_until(
        lambda: job.get_status().state
        not in [JobStatusStates.INITIALIZED, JobStatusStates.RUNNING],
        timeout=10,
        interval=0.1,
    )

    status = job.get_status()
    assert status.state == JobStatusStates.FINISHED

    output = "\n".join(status.loginfo["JobProgressUpdate"])
    # Make sure we get the generic background job output
    assert "Initialized background job" in output
    # Make sure we get the job specific output
    assert "Hallo :-)" in output


@pytest.mark.skip(reason="Fails randomly: see CMK-18161")
def test_stop_job() -> None:
    job = DummyBackgroundJob()
    job.start(
        job.execute_endless,
        InitialStatusArgs(
            title=job.gui_title(),
            deletable=False,
            stoppable=True,
            user=None,
        ),
    )

    wait_until(
        lambda: "Hanging loop" in job.get_status().loginfo["JobProgressUpdate"],
        timeout=10,
        interval=0.1,
    )

    status = job.get_status()
    assert status.state == JobStatusStates.RUNNING

    job.stop()

    status = job.get_status()
    assert status.state == JobStatusStates.STOPPED

    output = "\n".join(status.loginfo["JobProgressUpdate"])
    assert "Job was stopped" in output


@pytest.mark.usefixtures("request_context")
def test_job_status_not_started() -> None:
    job = DummyBackgroundJob()
    # Seems the attributes defined for the job, like "deletable" or "title" are not correct in
    # this stage. Looks like this should be changed.
    snapshot = job.get_status_snapshot()
    assert snapshot.has_exception is False
    assert snapshot.acknowledged_by is None
    assert job.is_available() is False
    assert job.is_deletable() is True
    assert job.is_visible() is True
    assert job.may_stop() is False
    assert job.may_delete() is False
    assert job.is_active() is False
    assert job.exists() is False
    assert job.get_job_id() == "dummy_job"
    assert job.get_title() == "Background job"


@pytest.mark.skip(reason="Fails randomly: see CMK-18161")
@pytest.mark.usefixtures("request_context")
def test_job_status_while_running() -> None:
    job = DummyBackgroundJob()
    job.start(
        job.execute_endless,
        InitialStatusArgs(
            title=job.gui_title(),
            deletable=False,
            stoppable=True,
            user=None,
        ),
    )
    wait_until(
        lambda: "Hanging loop" in job.get_status().loginfo["JobProgressUpdate"],
        timeout=10,
        interval=0.1,
    )

    snapshot = job.get_status_snapshot()
    assert snapshot.has_exception is False
    assert snapshot.acknowledged_by is None
    assert job.is_available() is True
    assert job.is_deletable() is False
    assert job.is_visible() is True
    assert job.may_stop() is False
    assert job.may_delete() is False
    assert job.is_active() is True
    assert job.exists() is True
    assert job.get_job_id() == "dummy_job"
    assert job.get_title() == "Dummy Job"
    job.stop()


@pytest.mark.skip(reason="Fails randomly: see CMK-18161")
@pytest.mark.usefixtures("request_context")
def test_job_status_after_stop() -> None:
    job = DummyBackgroundJob()
    job.start(
        job.execute_endless,
        InitialStatusArgs(
            title=job.gui_title(),
            deletable=False,
            stoppable=True,
            user=None,
        ),
    )
    wait_until(
        lambda: "Hanging loop" in job.get_status().loginfo["JobProgressUpdate"],
        timeout=20,
        interval=0.1,
    )
    job.stop()

    status = job.get_status()
    assert status.state == JobStatusStates.STOPPED

    snapshot = job.get_status_snapshot()
    assert snapshot.has_exception is False
    assert snapshot.acknowledged_by is None
    assert job.is_available() is True
    assert job.is_deletable() is False
    assert job.is_visible() is True
    assert job.may_stop() is False
    assert job.may_delete() is False
    assert job.is_active() is False
    assert job.exists() is True
    assert job.get_job_id() == "dummy_job"
    assert job.get_title() == "Dummy Job"


def test_running_job_ids_none() -> None:
    assert not running_job_ids(logging.getLogger())


@pytest.mark.skip(reason="Takes too long: see CMK-18161")
def test_running_job_ids_one_running() -> None:
    job = DummyBackgroundJob()
    job.start(
        job.execute_endless,
        InitialStatusArgs(
            title=job.gui_title(),
            deletable=False,
            stoppable=True,
            user=None,
        ),
    )
    wait_until(
        lambda: "Hanging loop" in job.get_status().loginfo["JobProgressUpdate"],
        timeout=20,
        interval=0.1,
    )

    try:
        assert running_job_ids(logging.getLogger()) == ["dummy_job"]
    finally:
        job.stop()


@pytest.mark.skip(reason="Takes too long: see CMK-18161")
def test_wait_for_background_jobs_while_one_running_for_too_long(
    caplog: pytest.LogCaptureFixture,
) -> None:
    job = DummyBackgroundJob()
    job.start(
        job.execute_endless,
        InitialStatusArgs(
            title=job.gui_title(),
            deletable=False,
            stoppable=True,
            user=None,
        ),
    )
    wait_until(
        lambda: "Hanging loop" in job.get_status().loginfo["JobProgressUpdate"],
        timeout=20,
        interval=0.1,
    )

    try:
        with caplog.at_level(logging.INFO):
            try:
                job_registry.register(DummyBackgroundJob)
                wait_for_background_jobs(logging.getLogger(), timeout=1)
            finally:
                job_registry.unregister("DummyBackgroundJob")

        logs = [rec.message for rec in caplog.records]
        assert "Waiting for dummy_job to finish..." in logs
        assert "WARNING: Did not finish within 1 seconds" in logs
    finally:
        job.stop()


@pytest.mark.skip(reason="Takes too long: see CMK-18161")
def test_wait_for_background_jobs_while_one_running_but_finishes(
    caplog: pytest.LogCaptureFixture,
) -> None:
    job = DummyBackgroundJob()
    job.start(
        job.execute_endless,
        InitialStatusArgs(
            title=job.gui_title(),
            deletable=False,
            stoppable=True,
            user=None,
        ),
    )
    wait_until(
        lambda: "Hanging loop" in job.get_status().loginfo["JobProgressUpdate"],
        timeout=20,
        interval=0.1,
    )

    with caplog.at_level(logging.INFO):
        try:
            job_registry.register(DummyBackgroundJob)
            threading.Thread(target=job.stop).start()
            wait_for_background_jobs(logging.getLogger(), timeout=2)
        finally:
            job_registry.unregister("DummyBackgroundJob")

    logs = [rec.message for rec in caplog.records]
    assert "Waiting for dummy_job to finish..." in logs
    assert "WARNING: Did not finish within 2 seconds" not in logs
