#!/usr/bin/env python

# DataSender.py
#
# Copyright (C) 2014 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
# Functions related to sending feedback data
#

import json
import os
import datetime

import kano.logging as logging
from kano.utils import run_cmd
from kano_world.connection import request_wrapper, content_type_json
from kano_world.functions import get_email
from kano_profile.badges import increment_app_state_variable_with_dialog
import base64


def send_data(text, fullInfo):

    meta = {
        'kanux_version': get_version()
    }

    if fullInfo:
        meta['process'] = get_process()
        meta['packages'] = get_packages()
        meta['dmesg'] = get_dmesg()
        meta['syslog'] = get_syslog()
        meta['wpalog'] = get_wpalog()
        meta['cmdline-config'] = get_cmdline_config()
        meta['wlaniface'] = get_wlaniface()
        meta['kwificache'] = get_kwifi_cache()
        meta['usbdevices'] = get_usb_devices()
        meta['screenshot'] = get_screenshot()
        meta['app-logs'] = get_app_logs()
        meta['hdmi-info'] = get_hdmi_info()

    payload = {
        'text': text,
        'email': get_email(),
        'category': 'os',
        'meta': meta
    }

    success, error, data = request_wrapper('post', '/feedback', data=json.dumps(payload), headers=content_type_json)
    if not success:
        return False, error
    if fullInfo:
        # kano-profile stat collection
        increment_app_state_variable_with_dialog('kano-feedback', 'bugs_submitted', 1)

        # logs were sent, clean up
        logging.cleanup()

    return True, None


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
    cmd = "tail -v -n 100 /var/log/messages"
    o, _, _ = run_cmd(cmd)
    return o


def get_wpalog():
    cmd = "tail -n 80 /var/log/kano_wpa.log"
    o, _, _ = run_cmd(cmd)
    return o


def get_cmdline_config():
    cmd = "cat /boot/cmdline.txt /boot/config.txt"
    o, _, _ = run_cmd(cmd)
    return o


def get_wlaniface():
    cmd = "iwconfig wlan0"
    o, _, _ = run_cmd(cmd)
    return o


def get_app_logs():
    logs = logging.read_logs()

    output = ""
    for f, data in logs.iteritems():
        app_name = os.path.basename(f).split(".")[0]
        output += "LOGFILE: {}\n".format(f)
        for line in data:
            line["time"] = datetime.datetime.fromtimestamp(line["time"]).isoformat()
            output += "{time} {app} {level}: {message}\n".format(app=app_name, **line)

    return output


def get_kwifi_cache():
    # We do not collect sensitive private information - Keypass is sent as "obfuscated" literal
    cmd = "cat /etc/kwifiprompt-cache.conf | sed 's/\"enckey\":.*/\"enckey\": \"obfuscated\"/'"
    o, _, _ = run_cmd(cmd)
    return o


def get_usb_devices():
    # Gives us 2 short lists of usb devices, first one with deviceIDs and manufacturer strings
    # Second one in hierarchy mode along with matching kernel drivers controlling each device
    # So we will know for a wireless dongle which kernel driver linux decides to load. Same for HIDs.
    cmd = "lsusb && lsusb -t"
    o, _, _ = run_cmd(cmd)
    return o


def get_screenshot():
    file_path = "/tmp/feedback.png"
    cmd = "kano-screenshot -w 1024 -p " + file_path
    _, _, rc = run_cmd(cmd)
    if rc == 0:
        # Convert image to string
        with open(file_path, "rb") as imageFile:
            str = base64.b64encode(imageFile.read())
            return str
    return ""


def get_hdmi_info():
    cmd = "tvservice -d edid.dat && edidparser edid.dat"
    o, _, _ = run_cmd(cmd)
    return o


def sanitise_input(text):
    # Replace double quotation mark for singles
    text = text.replace('"', "'")
    # Fix upload error when data field begins with " or '
    if text[:1] == '"' or text[:1] == "'":
        text = " " + text
    return text
