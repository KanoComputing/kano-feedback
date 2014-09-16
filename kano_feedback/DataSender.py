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
from kano.utils import run_cmd, write_file_contents, ensure_dir, delete_dir, delete_file, \
    read_file_contents
from kano_world.connection import request_wrapper
from kano_world.functions import get_email
from kano_profile.badges import increment_app_state_variable_with_dialog


TMP_DIR = '/tmp/kano-feedback/'
SCREENSHOT_NAME = 'screenshot.png'
SCREENSHOT_PATH = TMP_DIR + SCREENSHOT_NAME


def send_data(text, fullInfo, subject=""):
    files = {}

    if fullInfo:
        files['report'] = get_metadata_archive()

    payload = {
        "text": text,
        "email": get_email(),
        "category": "os",
        "subject": subject,
        "app_logs": get_app_logs_dict(),
    }

    # send the bug report and remove all the created files
    success, error, data = request_wrapper('post', '/feedback', data=payload, files=files)
    delete_tmp_dir()

    if not success:
        return False, error
    if fullInfo:
        # kano-profile stat collection
        increment_app_state_variable_with_dialog('kano-feedback', 'bugs_submitted', 1)

        # logs were sent, clean up
        logging.cleanup()

    return True, None


def delete_tmp_dir():
    delete_dir(TMP_DIR)


def create_tmp_dir():
    ensure_dir(TMP_DIR)


def delete_screenshot():
    delete_file(SCREENSHOT_PATH)


def get_metadata_archive():
    ensure_dir(TMP_DIR)

    file_list = [
        {'name': 'kanux_version.txt', 'contents': get_version()},
        {'name': 'process.txt', 'contents': get_process()},
        {'name': 'packages.txt', 'contents': get_packages()},
        {'name': 'dmesg.txt', 'contents': get_dmesg()},
        {'name': 'syslog.txt', 'contents': get_syslog()},
        {'name': 'wpalog.txt', 'contents': get_wpalog()},
        {'name': 'cmdline.txt', 'contents': read_file_contents('/boot/cmdline.txt')},
        {'name': 'config.txt', 'contents': read_file_contents('/boot/config.txt')},
        {'name': 'wlaniface.txt', 'contents': get_wlaniface()},
        {'name': 'kwificache.txt', 'contents': get_kwifi_cache()},
        {'name': 'usbdevices.txt', 'contents': get_usb_devices()},
        {'name': 'app-logs.txt', 'contents': get_app_logs()},
        {'name': 'hdmi-info.txt', 'contents': get_hdmi_info()}
    ]

    if os.path.isfile(SCREENSHOT_PATH):
        file_list.append({
                         'name': SCREENSHOT_NAME,
                         'contents': read_file_contents(SCREENSHOT_PATH)
                         })

    # create files for each non empty metadata info
    for file in file_list:
        if file['contents']:
            write_file_contents(TMP_DIR + file['name'], file['contents'])

    # archive all the metadata files - need to change dir to avoid tar subdirectories
    archive_path = 'bug_report.tar.gz'
    current_directory = os.getcwd()
    os.chdir(TMP_DIR)
    run_cmd("tar -zcvf {} *".format(archive_path))

    # open the file and return it
    archive = open(archive_path, 'rb')

    # restore the current working directory
    os.chdir(current_directory)
    return archive


def get_version():
    cmd = "ls -l /etc/kanux_version | awk '{ print $6 \" \" $7 \" \" $8 }' && cat /etc/kanux_version"
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


def get_app_logs_dict():
    logs = logging.read_logs()

    logs_dict = dict()

    for f, data in logs.iteritems():
        if not data:
            continue
        app_name = os.path.basename(f).split(".")[0]
        for line in data:
            line["time"] = datetime.datetime.fromtimestamp(line["time"]).isoformat()
        logs_dict[app_name] = data

    return logs_dict


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
    ensure_dir(TMP_DIR)
    cmd = "kano-screenshot -w 1024 -p " + SCREENSHOT_PATH
    _, _, rc = run_cmd(cmd)


def copy_screenshot(filename):
    ensure_dir(TMP_DIR)
    if os.path.isfile(filename):
        run_cmd("cp %s %s" % (filename, SCREENSHOT_PATH))


def sanitise_input(text):
    # Replace double quotation mark for singles
    text = text.replace('"', "'")
    # Fix upload error when data field begins with " or '
    if text[:1] == '"' or text[:1] == "'":
        text = " " + text
    return text
