#!/usr/bin/env python

# DataSender.py
#
# Copyright (C) 2014 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
# Functions related to sending feedback data
#

import os
import datetime

import kano.logging as logging
from kano.utils import run_cmd, write_file_contents, ensure_dir, delete_dir, delete_file
from kano_world.connection import request_wrapper
from kano_world.functions import get_email
from kano_profile.badges import increment_app_state_variable_with_dialog


TMP_DIR = '/tmp/kano-feedback/'


def send_data(text, fullInfo):

    if fullInfo:
        archive = get_metadata_archive()

    payload = {
        "text": text,
        "email": get_email(),
        "category": "os"
    }

    success, error, data = request_wrapper('post', '/feedback', data=payload, files=archive)
    delete_dir(TMP_DIR)

    if not success:
        return False, error
    if fullInfo:
        # kano-profile stat collection
        increment_app_state_variable_with_dialog('kano-feedback', 'bugs_submitted', 1)

        # logs were sent, clean up
        logging.cleanup()

    return True, None


def get_metadata_archive():
    ensure_dir(TMP_DIR)
    write_file_contents(TMP_DIR + 'kanux_version.txt', get_version())
    write_file_contents(TMP_DIR + 'process.txt', get_process())
    write_file_contents(TMP_DIR + 'packages.txt', get_packages())
    write_file_contents(TMP_DIR + 'dmesg.txt', get_dmesg())
    write_file_contents(TMP_DIR + 'syslog.txt', get_syslog())
    write_file_contents(TMP_DIR + 'wpalog.txt', get_wpalog())
    write_file_contents(TMP_DIR + 'cmdline-config.txt', get_cmdline_config())
    write_file_contents(TMP_DIR + 'wlaniface.txt', get_wlaniface())
    write_file_contents(TMP_DIR + 'kwificache.txt', get_kwifi_cache())
    write_file_contents(TMP_DIR + 'usbdevices.txt', get_usb_devices())
    write_file_contents(TMP_DIR + 'app-logs.txt', get_app_logs())
    write_file_contents(TMP_DIR + 'hdmi-info.txt', get_hdmi_info())
    take_screenshot()

    archive_path = TMP_DIR + 'bug_report.tar.gz'
    cmd = "tar -zcvf {} {}".format(archive_path, TMP_DIR)
    _, error, return_code = run_cmd(cmd)

    if not return_code:
        archive = {
            'report': open(archive_path, 'rb')
        }
        return archive
    else:
        return None


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


def get_hdmi_info():
    file_path = TMP_DIR + 'edid.dat'
    cmd = "tvservice -d {} && edidparser {}".format(file_path, file_path)
    o, _, _ = run_cmd(cmd)
    delete_file(file_path)
    return o


def take_screenshot():
    file_path = TMP_DIR + 'feedback.png'
    cmd = "kano-screenshot -w 1024 -p " + file_path
    _, _, rc = run_cmd(cmd)


def sanitise_input(text):
    # Replace double quotation mark for singles
    text = text.replace('"', "'")
    # Fix upload error when data field begins with " or '
    if text[:1] == '"' or text[:1] == "'":
        text = " " + text
    return text
