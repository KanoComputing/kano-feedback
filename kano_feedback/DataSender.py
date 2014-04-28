#!/usr/bin/env python

# DataSender.py
#
# Copyright (C) 2014 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
# Functions related to sending feedback data
#

import sys
import json
from os.path import expanduser

from kano.utils import run_cmd, read_file_contents
from kano.world.connection import request_wrapper, content_type_json


def send_data(text, fullInfo):
    send_data_old(text, fullInfo)

    meta = {
        'kanux_version': get_version()
    }

    if fullInfo:
        meta['process'] = get_process()
        meta['packages'] = get_packages()
        meta['dmesg'] = get_dmesg()
        meta['syslog'] = get_syslog()

    payload = {
        'text': text,
        'email': get_email(),
        'category': 'os',
        'meta': meta
    }

    success, error, data = request_wrapper('post', '/feedback', data=json.dumps(payload), headers=content_type_json)
    if not success:
        return False, error
    return True, None


def send_data_old(text, fullInfo):
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
    email = read_file_contents(email_path)
    if not email:
        msg = "We haven't got your email.\n \
1) Go to Settings\n \
2) Introduce a valid email address\n\n \
Now we can reply back to you!"
        run_cmd('zenity --info --text "{}"'.format(msg))
        sys.exit()
    return email


def sanitise_input(text):
    # Replace double quotation mark for singles
    text = text.replace('"', "'")
    # Fix upload error when data field begins with " or '
    if text[:1] == '"' or text[:1] == "'":
        text = " " + text
    return text
