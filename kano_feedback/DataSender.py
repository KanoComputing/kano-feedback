#!/usr/bin/env python

# DataSender.py
#
# Copyright (C) 2014 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
# Functions related to sending feedback data
#

from kano.utils import run_cmd
from os.path import expanduser


def send_data(text, fullInfo):

    dataToSend = ''
    # Email entry
    dataToSend += 'entry.1110323866'
    dataToSend += '='
    dataToSend += sanitise_input(get_email())
    dataToSend += '&'
    # Response entry
    dataToSend += 'entry.162771870'
    dataToSend += '='
    dataToSend += sanitise_input(text)
    dataToSend += '&'
    # Kanux version entry
    dataToSend += 'entry.1932769824'
    dataToSend += '='
    dataToSend += sanitise_input(get_version())
    dataToSend += '&'
    # TODO: remove Category column
    dataToSend += 'entry.1341620943'
    dataToSend += '='
    dataToSend += 'Refactored'
    if fullInfo:
        dataToSend += '&'
        # Running Processes
        dataToSend += 'entry.868132968'
        dataToSend += '='
        dataToSend += sanitise_input(get_process())
        dataToSend += '&'
        # Installed Packages
        dataToSend += 'entry.1747707726'
        dataToSend += '='
        dataToSend += sanitise_input(get_packages())
        dataToSend += '&'
        # Dmesg
        dataToSend += 'entry.1892657243'
        dataToSend += '='
        dataToSend += sanitise_input(get_dmesg())
        dataToSend += '&'
        # Syslog
        dataToSend += 'entry.355029695'
        dataToSend += '='
        dataToSend += sanitise_input(get_syslog())

    # Send data
    form = 'https://docs.google.com/a/kano.me/forms/d/1PqWb05bQjjuHc41cA0m2f0jFgidUw_c5H53IQeaemgo/formResponse'
    cmd = 'curl --progress-bar -d \"%s\" %s' % (dataToSend, form)
    o, e, rc = run_cmd(cmd)
    if rc != 0:
        return False
    return True


def get_version():
    cmd = "ls -l /etc/kanux_version | awk '{ print $6 \" \" $7 \" \" $8 }'"
    o, _, _ = run_cmd(cmd)
    return o


def get_process():
    cmd = "ps -e | awk '{ print $4 }'"
    o, _, _ = run_cmd(cmd)
    return o


def get_packages():
    cmd = "dpkg-query -l | awk '{ print $2 \"-\" $3 }'"
    o, _, _ = run_cmd(cmd)
    return o


def get_dmesg():
    cmd = "dmesg"
    o, _, _ = run_cmd(cmd)
    return o


def get_syslog():
    cmd = "tail -n 100 /var/log/messages"
    o, _, _ = run_cmd(cmd)
    return o


def get_email():
    email_path = expanduser("~") + "/.useremail"

    with open(email_path, 'r') as f:
        return f.readline()
    return ""


def sanitise_input(text):
    # Replace double quotation mark for singles
    text = text.replace('"', "'")
    # Fix upload error when data field begins with " or '
    if text[:1] == '"' or text[:1] == "'":
        text = " " + text
    return text
