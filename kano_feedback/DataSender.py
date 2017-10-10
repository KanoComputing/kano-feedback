#!/usr/bin/env python

# DataSender.py
#
# Copyright (C) 2014-2017 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#
# Functions related to sending feedback data


import os
from os.path import expanduser
import datetime
import json

# Do not Import Gtk if we are not bound to an X Display
if os.environ.has_key('DISPLAY'):
    from gi.repository import Gtk

import kano.logging as logging
from kano.utils import run_cmd, write_file_contents, ensure_dir, delete_dir, delete_file, \
    read_file_contents
from kano_world.connection import request_wrapper, content_type_json
from kano_world.functions import get_email, get_mixed_username
from kano_profile.badges import increment_app_state_variable_with_dialog
from kano.logging import logger
from kano.utils import get_rpi_model

# Do not Import Gtk if we are not bound to an X Display
if os.environ.has_key('DISPLAY'):
    from kano.gtk3.kano_dialog import KanoDialog

from kano_world.functions import is_registered
from kano.network import is_internet
from kano_content.api import ContentManager

TMP_DIR = os.path.join(expanduser('~'), '.kano-feedback/')
SCREENSHOT_NAME = 'screenshot.png'
SCREENSHOT_PATH = TMP_DIR + SCREENSHOT_NAME
ARCHIVE_NAME = 'bug_report.tar.gz'


def send_data(text, full_info, subject="", network_send=True):
    '''
    Sends the data to our servers through a post request
    '''
    files = {}
    # packs all the information into 'files'
    if full_info:
        files['report'] = get_metadata_archive()
    # This is the actual info: subject, text, email, username
    payload = {
        "text": text,
        "email": get_email(),
        "username": get_mixed_username(),
        "category": "os",
        "subject": subject
    }

    if not network_send:
        return True, None

    # send the bug report and remove all the created files
    success, error, data = request_wrapper('post', '/feedback',
                                           data=payload, files=files)
    delete_tmp_dir()

    if not success:
        return False, error
    if full_info:
        # kano-profile stat collection
        increment_app_state_variable_with_dialog('kano-feedback',
                                                 'bugs_submitted', 1)
        # logs were sent, clean up
        logging.cleanup()

    return True, None


def delete_tmp_dir():
    '''
    Deletes TMP_DIR directory
    '''
    delete_dir(TMP_DIR)


def create_tmp_dir():
    '''
    Creates TMP_DIR directory
    '''
    ensure_dir(TMP_DIR)


def delete_screenshot():
    '''
    Deletes the SCREENSHOT_PATH file
    '''
    delete_file(SCREENSHOT_PATH)


def get_metadata_archive():
    '''
    It creates a file (ARCHIVE_NAME) with all the information
    Returns the file
    '''
    ensure_dir(TMP_DIR)
    file_list = [
        {'name': 'kanux_version.txt', 'contents': get_version()},
        {'name': 'process.txt', 'contents': get_processes()},
        {'name': 'packages.txt', 'contents': get_packages()},
        {'name': 'dmesg.txt', 'contents': get_dmesg()},
        {'name': 'syslog.txt', 'contents': get_syslog()},
        {'name': 'cmdline.txt', 'contents': read_file_contents('/boot/cmdline.txt')},
        {'name': 'config.txt', 'contents': read_file_contents('/boot/config.txt')},
        {'name': 'wifi-info.txt', 'contents': get_wifi_info()},
        {'name': 'usbdevices.txt', 'contents': get_usb_devices()},

        # TODO: Remove raw logs when json ones become stable
        {'name': 'app-logs.txt', 'contents': get_app_logs_raw()},

        {'name': 'app-logs-json.txt', 'contents': get_app_logs_json()},
        {'name': 'hdmi-info.txt', 'contents': get_hdmi_info()},
        {'name': 'xorg-log.txt', 'contents': get_xorg_log()},
        {'name': 'cpu-info.txt', 'contents': get_cpu_info()},
        {'name': 'lsof.txt', 'contents': get_lsof()},
        {'name': 'content-objects.txt', 'contents': get_co_list()}
    ]
    # Include the screenshot if it exists
    if os.path.isfile(SCREENSHOT_PATH):
        file_list.append({
                         'name': SCREENSHOT_NAME,
                         'contents': read_file_contents(SCREENSHOT_PATH)
                         })
    # create files for each non empty metadata info
    for file in file_list:
        if file['contents']:
            write_file_contents(TMP_DIR + file['name'], file['contents'])
    # Collect all coredumps, for applications that terminated unexpectedly
    for f in os.listdir('/var/tmp/'):
        if f.startswith('core-'):
            file_list.append({
                'name': f,
                'contents': read_file_contents(os.path.join('/var/tmp', f))
            })
    # archive all the metadata files
    # need to change dir to avoid tar subdirectories
    current_directory = os.getcwd()
    os.chdir(TMP_DIR)
    run_cmd("tar -zcvf {} *".format(ARCHIVE_NAME))
    # open the file and return it
    archive = open(ARCHIVE_NAME, 'rb')
    # restore the current working directory
    os.chdir(current_directory)

    return archive


def get_version():
    '''
    Return a string with the current version of the OS.
    Uses the command kanux_version
    '''
    cmd = "ls -l /etc/kanux_version | awk '{ print $6 \" \" $7 \" \" $8 }' && cat /etc/kanux_version"
    o, _, _ = run_cmd(cmd)

    return o


def get_processes():
    '''
    Returns a string with the current processes running in the system
    '''
    cmd = "ps -aux"
    o, _, _ = run_cmd(cmd)

    return o


def get_packages():
    '''
    Returns a string with the list of packages installed in the system
    '''
    cmd = "dpkg-query -l | awk '{ print $2 \"-\" $3 }'"
    o, _, _ = run_cmd(cmd)

    return o


def get_dmesg():
    '''
    Returns a string with dmesg and uptime info
    '''
    cmd_dmesg = "dmesg"
    cmd_uptime = "uptime"
    d, _, _ = run_cmd(cmd_dmesg)
    t, _, _ = run_cmd(cmd_uptime)
    t = 'system uptime: %s' % t

    return '%s\n%s' % (d, t)


def get_syslog():
    '''
    Returns the last 100 lines of syslog messages
    '''
    cmd = "tail -v -n 100 /var/log/messages"
    o, _, _ = run_cmd(cmd)

    return o


def get_wpalog():
    '''
    Returns the last 300 lines of the wpa log
    '''
    cmd = "tail -n 300 /var/log/kano_wpa.log"
    o, _, _ = run_cmd(cmd)

    return o


def get_wlaniface():
    '''
    Retruns a string with wlan info
    '''
    cmd = "/sbin/iwconfig wlan0"
    o, _, _ = run_cmd(cmd)

    return o


def get_xorg_log():
    '''
    Returns a string with the Xorg log
    '''
    cmd = "cat /var/log/Xorg.0.log"
    o, _, _ = run_cmd(cmd)

    return o


def get_cpu_info():
    '''
    Returns a string with the cpuid and the board model
    '''
    cmd = "/usr/bin/rpi-info"
    o, _, _ = run_cmd(cmd)
    o += '\nModel: {}'.format(get_rpi_model())

    return o


def get_lsof():
    '''
    Get lsof information (list of open files)
    '''
    cmd = "sudo /usr/bin/lsof"
    o, _, _ = run_cmd(cmd)

    return o


def get_app_logs_raw():
    '''
    Extract kano logs in raw format:
    "LOGFILE: component" (one line per component)
    followed by entries in the form:
    "2014-09-30T10:18:54.532015 kano-updater info: Return value: 0"
    '''
    logs = logging.read_logs()
    output = ""
    for f, data in logs.iteritems():
        app_name = os.path.basename(f).split(".")[0]
        output += "LOGFILE: {}\n".format(f)
        for line in data:
            line["time"] = datetime.datetime.fromtimestamp(line["time"]).isoformat()
            output += "{time} {app} {level}: {message}\n".format(app=app_name, **line)

    return output


def get_app_logs_json():
    '''
    Return a JSON stream with the kano logs
    '''
    # Fetch the kano logs
    kano_logs = logging.read_logs()

    # Transform them into a sorted, indented json stream
    kano_logs_json = json.dumps(kano_logs, sort_keys=True, indent=4,
                                separators=(',', ': '))
    return kano_logs_json


def get_kwifi_cache():
    '''
    Send wifi cache data
    NOTE: We do not collect sensitive private information.
    Keypass is sent as "obfuscated" literal.
    '''
    cmd = "cat /etc/kwifiprompt-cache.conf | sed 's/\"enckey\":.*/\"enckey\": \"obfuscated\"/'"
    o, _, _ = run_cmd(cmd)

    return o


def get_usb_devices():
    '''
    Gives us 2 short lists of usb devices:
    1) deviceIDs and manufacturer strings
    2) Hierarchy mode along with matching kernel drivers controlling each device
    We can know for wireless dongles and HIDs which kernel driver is loaded.
    '''
    cmd = "lsusb && lsusb -t"
    o, _, _ = run_cmd(cmd)

    return o


def get_networks_info():
    '''
    Returns a string with ifconfig info
    '''
    cmd = "/sbin/ifconfig"
    o, _, _ = run_cmd(cmd)

    return o


def get_wifi_info():
    '''
    Returns a string with wifi specific info
    '''
    # Get username here
    world_username = "Kano World username: {}\n\n".format(get_mixed_username())
    kwifi_cache = "**kwifi_cache**\n {}\n\n".format(get_kwifi_cache())
    wlaniface = "**wlaniface**\n {}\n\n".format(get_wlaniface())
    ifconfig = "**ifconfig**\n {}\n\n".format(get_networks_info())
    wpalog = "**wpalog**\n {}\n\n".format(get_wpalog())

    return world_username + kwifi_cache + wlaniface + ifconfig + wpalog


def get_hdmi_info():
    '''
    Returns a string with Display info
    '''
    # Current resolution
    cmd = "tvservice -s"
    o, _, _ = run_cmd(cmd)
    res = 'Current resolution: {}\n\n'.format(o)
    # edid file
    file_path = TMP_DIR + 'edid.dat'
    cmd = "tvservice -d {} && edidparser {}".format(file_path, file_path)
    edid, _, _ = run_cmd(cmd)
    delete_file(file_path)

    return res + edid


def get_co_list():
    '''
    Returns a list of content object IDs currently on the system.
    '''
    try:
        cm = ContentManager.from_local()
        objects = cm.list_local_objects(active_only=False, inactive_only=False)
        return str(objects)
    except:
        return "Couldn't get a list of content objects."


def take_screenshot():
    '''
    Takes a screenshot and saves it into SCREENSHOT_PATH
    '''
    ensure_dir(TMP_DIR)
    cmd = "kano-screenshot -w 1024 -p " + SCREENSHOT_PATH
    _, _, rc = run_cmd(cmd)


def copy_screenshot(filename):
    '''
    Copies screenshot 'filename' into SCREENSHOT_PATH
    '''
    ensure_dir(TMP_DIR)
    if os.path.isfile(filename):
        run_cmd("cp %s %s" % (filename, SCREENSHOT_PATH))


def copy_archive_report(target_archive):
    '''
    Copies source archive (TMP_DIR/ARCHIVE_NAME) into target_archive
    '''
    ensure_dir(TMP_DIR)
    source_archive = os.path.join(TMP_DIR, ARCHIVE_NAME)
    if os.path.isfile(source_archive):
        _, _, rc = run_cmd("cp %s %s" % (source_archive, target_archive))
        return (rc == 0)
    else:
        return False


def sanitise_input(text):
    '''
    Cleans a string(text) from double quotes
    '''
    # Replace double quotation mark for singles
    text = text.replace('"', "'")
    # Fix upload error when data field begins with " or '
    if text[:1] == '"' or text[:1] == "'":
        text = " " + text
    return text


def try_login():
    '''
    Returns login status.
    If user is not logged in the first time, the logger will be launched
    '''
    # Check if user is registered
    if not is_registered():
        _, _, rc = run_cmd('kano-login 3', localised=True)

    return is_registered()


def try_connect():
    '''
    Returns internet status.
    If connection fails the first time, the WiFi config will be launched
    '''
    if is_internet():
        return True

    run_cmd('sudo /usr/bin/kano-settings 12', localised=True)

    return is_internet()


def send_question_response(answers, interactive=True, tags=['os', 'feedback-widget'],
                           debug=False, dry_run=False):
    '''
    This function is used by the Feedback widget to network-send the responses.
    The information (question_id, answer, username and email) is sent to a Kano API endpoint.

    answers is a list of tuples each having a Question ID and an Answer literal.

    The answers will be all packed into a payload object and sent in one single network transaction.
    '''

    ok_msg_title = _('Thank you')
    ok_msg_body = _('We will use your feedback to improve your experience')

    if interactive and not try_connect() or not try_login():
        # The answer will be saved as offline, act as if it was sent correctly
        thank_you = KanoDialog(ok_msg_title, ok_msg_body)
        thank_you.dialog.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        thank_you.run()

        return False

    payload = {
        'email': get_email(),
        'username': get_mixed_username(),
        'answers': [
            { 'question_id': answer[0],
              'text': answer[1],
              'tags': tags } for answer in answers
        ]
    }

    if debug:
        print 'PAYLOAD construction:'
        print json.dumps(payload, sort_keys=True,
                         indent=4, separators=(',', ': '))

    # Send the answers unless we are testing the API
    if dry_run:
        return True

    success, error, dummy = request_wrapper('post', '/questions/responses',
                                            data=json.dumps(payload),
                                            headers=content_type_json)

    # Retry on error only if in GUI mode
    if not success:
        logger.error('Error while sending feedback: {}'.format(error))

        if not interactive:
            return False

        retry = KanoDialog(
            title_text=_('Unable to send'),
            description_text=_('Error while sending your feedback. Do you want to retry?'),
            button_dict={
                _('Close feedback').upper():
                    {
                        'return_value': False,
                        'color': 'red'
                    },
                _('Retry').upper():
                    {
                        'return_value': True,
                        'color': 'green'
                    }
            }
        )

        if retry.run():
            # Try again until they say no
            return send_question_response([(answer[0], answer)], interactive=interactive)

        return False

    if interactive:
        thank_you = KanoDialog(ok_msg_title, ok_msg_body)
        thank_you.dialog.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        thank_you.run()

    return True
