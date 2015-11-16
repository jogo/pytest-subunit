# -*- coding: utf-8 -*-
# inspired by https://github.com/Frozenball/pytest-sugar
import datetime
import os

from subunit import StreamResultToBytes
from subunit.test_results import AutoTimingTestResultDecorator

import py
import pytest
from _pytest.terminal import TerminalReporter
from _pytest._pluggy import HookspecMarker

hookspec = HookspecMarker("pytest")


def pytest_collection_modifyitems(session, config, items):
    if config.option.subunit:
        terminal_reporter = config.pluginmanager.getplugin('terminalreporter')
        terminal_reporter.tests_count += len(items)


def pytest_deselected(items):
    """ Update tests_count to not include deselected tests """
    if len(items) > 0:
        pluginmanager = items[0].config.pluginmanager
        terminal_reporter = pluginmanager.getplugin('terminalreporter')
        if (hasattr(terminal_reporter, 'tests_count')
                and terminal_reporter.tests_count > 0):
            terminal_reporter.tests_count -= len(items)


def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting", "reporting", after="general")
    group._addoption(
        '--subunit', action="store_true", dest="subunit", default=False,
        help=(
            "enable pytest-subunit"
        )
    )


@pytest.mark.trylast
def pytest_configure(config):
    if config.option.subunit:
        # Get the standard terminal reporter plugin and replace it with our
        standard_reporter = config.pluginmanager.getplugin('terminalreporter')
        subunit_reporter = SubunitTerminalReporter(standard_reporter)
        config.pluginmanager.unregister(standard_reporter)
        config.pluginmanager.register(subunit_reporter, 'terminalreporter')

_ZERO = datetime.timedelta(0)

class UTC(datetime.tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return _ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return _ZERO

utc = UTC()

class SubunitTerminalReporter(TerminalReporter):
    def __init__(self, reporter):
        TerminalReporter.__init__(self, reporter.config)
        self.writer = self._tw
        self.tests_count = 0
        self.reports = []
        self.result = StreamResultToBytes(self.writer._file)

    def _get_test_id(self, location):
        return location[0] + '::' + location[2]

    def pytest_collectreport(self, report):
        pass

    def pytest_collection_finish(self, session):
        if self.config.option.collectonly:
            self._printcollecteditems(session.items)

    def pytest_collection(self):
        # Prevent shoving `collecting` message
        pass

    def report_collect(self, final=False):
        # Prevent shoving `collecting` message
        pass

    def pytest_sessionstart(self, session):
        pass

    def pytest_runtest_logstart(self, nodeid, location):
        pass

    def pytest_sessionfinish(self, session, exitstatus):
        # always exit with exitcode 0
        session.exitstatus = 0

    def pytest_runtest_logreport(self, report):
        now = datetime.datetime.now(utc)
        self.reports.append(report)
        test_id = self._get_test_id(report.location)
        if report.when in ['setup', 'session']:
            if report.outcome == 'passed':
                self.result.status(test_id=test_id, test_status='exists')
                self.result.status(test_id=test_id, test_status='inprogress', timestamp=now)
            elif report.outcome == 'failed':
                import ipdb;ipdb.set_trace()
                pass
            else:
                import ipdb;ipdb.set_trace()
        elif report.when in ['call']:
            if report.outcome == 'passed':
                self.result.status(test_id=test_id, test_status='success', timestamp=now)
            elif report.outcome == 'failed':
                writer=py.io.TerminalWriter(stringio=True)
                report.toterminal(writer)
                writer.stringio.seek(0)
                out = writer.stringio.read()
                self.result.status(file_name=report.fspath, file_bytes=str(out), mime_type="text/plain; charset=utf8", test_id=test_id, test_status='fail', timestamp=now)
            else:
                self.result.status(test_id=test_id, test_status='skip', timestamp=now)
        elif report.when in ['teardown']:
            if report.outcome == 'passed':
                pass
            elif report.outcome == 'failed':
                import ipdb;ipdb.set_trace()
                pass
            else:
                import ipdb;ipdb.set_trace()
        else:
            raise Exception(str(report))

    def _printcollecteditems(self, items):
        for item in items:
            test_id = self._get_test_id(item.location)
            self.result.status(test_id=test_id, test_status='exists')

    def summary_stats(self):
        pass

    def summary_failures(self):
        # Prevent failure summary from being shown since we already
        # show the failure instantly after failure has occured.
        pass

    def summary_errors(self):
        # Prevent error summary from being shown since we already
        # show the error instantly after error has occured.
        pass

    def print_failure(self, report):
        # https://github.com/Frozenball/pytest-sugar/issues/34
        if hasattr(report, 'wasxfail'):
            return

        if self.config.option.tbstyle != "no":
            if self.config.option.tbstyle == "line":
                line = self._getcrashline(report)
                self.write_line(line)
            else:
                msg = self._getfailureheadline(report)
                if not hasattr(report, 'when'):
                    msg = "ERROR collecting " + msg
                elif report.when == "setup":
                    msg = "ERROR at setup of " + msg
                elif report.when == "teardown":
                    msg = "ERROR at teardown of " + msg
                self.write_line('')
                self.write_sep("―", msg)
                self._outrep_summary(report)