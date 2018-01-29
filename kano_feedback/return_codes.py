# return_codes.py
#
# Copyright (C) 2018 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#
# Return codes of binaries used throughout this project.


class RC(object):
    """Return codes of binaries used throughout this project. See ``source``
    for more details."""

    SUCCESS = 0

    INCORRECT_ARGS = 1

    # kano-feedback-cli specific.
    ERROR_SEND_DATA = 10
    ERROR_COPY_ARCHIVE = 11
