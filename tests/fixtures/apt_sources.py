#
# apt_sources.py
#
# Copyright (C) 2018-2019 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#
# Test fixtures to simulate apt sources files
#


import os
import pytest

from tests.fixtures.helpers import powerset, FakeFile


class AptSrcFile(FakeFile):
    def __repr__(self):
        return 'AptSrcFile({})'.format(self.filepath)


APT_DIR = '/etc/apt'
APT_SRC_DIR = os.path.join(APT_DIR, 'sources.list.d')

APT_SRC_FILES = [
    AptSrcFile(os.path.join(APT_DIR, 'sources.list')),
    AptSrcFile(os.path.join(APT_SRC_DIR, 'kano.list')),
    AptSrcFile(os.path.join(APT_SRC_DIR, 'collabora.list')),
]


@pytest.fixture(scope='function', params=powerset(APT_SRC_FILES),
                ids=[str(log) for log in powerset(APT_SRC_FILES)]
)
def apt_sources(fs, request):
    sources = sorted(request.param)

    for source in sources:
        fs.create_file(
            source.filepath,
            contents=source.contents
        )

    return sources
