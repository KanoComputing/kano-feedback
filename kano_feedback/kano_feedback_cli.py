# kano_feedback_cli.py
#
# Copyright (C) 2018 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#
# The main functionality of the kano-feedback-cli binary.


import os

from kano.utils.file_operations import touch

from kano_feedback.DataSender import send_data, take_screenshot, \
    copy_archive_report, delete_tmp_dir
from kano_feedback.utils import ensure_internet, ensure_kano_world_login
from kano_feedback.paths import Path
from kano_feedback.return_codes import RC


def _check_can_create_file_flag(flag_path):
    """TODO"""
    success = False
    try:
        if touch(flag_path):
            os.remove(flag_path)
            success = True
    except:
        pass
    return success


def main(args):
    """The main functionality of the kano-feedback-cli binary.

    Returns:
        int: Exit code as documented in :class:`.return_codes.RC`
    """

    if args['--flag'] and not _check_can_create_file_flag(args['--flag']):
        return RC.CANNOT_CREATE_FLAG

    report_file = args['--output'] or Path.DEFAULT_REPORT_PATH

    if args['--with-checks'] or args['--just-checks']:
        if not ensure_internet():
            return RC.NO_INTERNET

        if not ensure_kano_world_login():
            return RC.NO_KANO_WORLD_ACC

        if args['--just-checks']:
            return RC.SUCCESS

    if args['--screenshot']:
        print 'Taking a screenshot...'
        take_screenshot()

    print 'Gathering feedback data...'
    successful, error = send_data(
        args['--description'] or '',
        True,
        subject=args['--title'] or 'Kano OS: Feedback Report Logs',
        network_send=args['--send'],
        logs_path=args['--logs']
    )
    if not successful:
        print 'Error from send_data: {}'.format(error)
        return RC.ERROR_SEND_DATA

    if args['--flag']:
        print 'Creating file flag...'
        successful = touch(args['--flag'])
        if not successful:
            print 'Could not create file flag {}'.format(args['--flag'])
            return RC.ERROR_CREATE_FLAG

    successful = copy_archive_report(report_file)
    delete_tmp_dir()

    if successful:
        print 'Feedback file saved to:', report_file
    else:
        print 'Could not save feedback to:', report_file, \
              'Perhaps you need to use sudo?'
        return RC.ERROR_COPY_ARCHIVE

    return RC.SUCCESS
