#
# logs.py
#
# Copyright (C) 2019 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#
# Test fixtures to simulate log files
#


import pytest

from tests.fixtures.helpers import powerset, FakeFile


class DpkgLogFile(FakeFile):
    def __repr__(self):
        return 'DpkgLogFile({})'.format(self.filepath)


class AptLogFile(FakeFile):
    def __repr__(self):
        return 'AptLogFile({})'.format(self.filepath)


DPKG_LOG_FILES = [
    DpkgLogFile('/var/log/dpkg.log', log_filename='install-dpkg.log'),
]
APT_LOG_FILES = [
    AptLogFile('/var/log/apt/term.log', log_filename='install-term.log'),
    AptLogFile('/var/log/apt/history.log', log_filename='install-history.log'),
]


@pytest.fixture(
    scope='function', params=powerset(DPKG_LOG_FILES),
    ids=[str(log) for log in powerset(DPKG_LOG_FILES)]
)
def dpkg_logs(fs, request):
    log_files = request.param

    for log_file in log_files:
        fs.create_file(
            log_file.filepath,
            contents=log_file.contents
        )

    return log_files


@pytest.fixture(
    scope='function', params=powerset(APT_LOG_FILES),
    ids=[str(log) for log in powerset(APT_LOG_FILES)]
)
def apt_logs(fs, request):
    log_files = request.param

    for log_file in log_files:
        fs.create_file(
            log_file.filepath,
            contents=log_file.contents
        )

    return log_files
