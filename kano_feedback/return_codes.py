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
    NO_INTERNET = 2
    NO_KANO_WORLD_ACC = 3
    CANNOT_CREATE_FLAG = 4  # read-only fs?

    # kano-feedback-cli specific.
    ERROR_SEND_DATA = 10
    ERROR_COPY_ARCHIVE = 11
    ERROR_CREATE_FLAG = 12
