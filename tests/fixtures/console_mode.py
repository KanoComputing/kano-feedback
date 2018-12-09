#
# apt_sources.py
#
# Copyright (C) 2018 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#
# Test fixtures to allow non-GUI code execution
#


import pytest


@pytest.fixture(scope='function')
def console_mode(monkeypatch):
    monkeypatch.delenv('DISPLAY', raising=False)
