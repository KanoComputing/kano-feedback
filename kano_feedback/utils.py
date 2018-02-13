# utils.py
#
# Copyright (C) 2018 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#
# Utility functions used throughout this project.


from kano.network import is_internet
from kano_world.functions import login_using_token
from kano.utils.shell import run_cmd


def ensure_internet():
    """Ensure there is an internet connection.

    Check for an internet connection and uses ``kano-settings`` to configure
    one if not setup. If the popup subsequently fails, the operation quits.

    Returns:
        bool: Whether there is an internet connection
    """

    if not is_internet():
        run_cmd('sudo kano-settings --label no-internet', localised=True)
        return is_internet()

    return True


def ensure_kano_world_login():
    """Ensure user has logged in Kano World.

    Checks for a login session and uses ``kano-login`` to configure one if not
    setup. If the popup subsequently fails, the operation quits.

    Returns:
        bool: Whether there is a valid login session to Kano World
    """

    is_logged_in, error = login_using_token()

    if not is_logged_in:
        run_cmd('kano-login', localised=True)
        is_logged_in, error = login_using_token()
        return is_logged_in

    return True
