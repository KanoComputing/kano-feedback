#
# test_data_sender.py
#
# Copyright (C) 2018-2019 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#
# Tests that the data is correctly collected and sent
#


import imp


def test_get_sources_list(fix_toolset, console_mode, apt_sources):
    import kano_feedback.DataSender as DataSender
    # FIXME: Reload required to re-patch the module with the new fs
    imp.reload(DataSender)

    src_list = DataSender.get_sources_list()
    expected = '\n'.join([
        'Source file: {}\n{}\n{}\n{}\n'.format(
            src.filepath,
            DataSender.SEPARATOR,
            src.contents,
            DataSender.SEPARATOR,
        )
        for src in apt_sources
    ])
    assert src_list == expected


def test_get_install_logs(console_mode, dpkg_logs, apt_logs):
    import kano_feedback.DataSender as DataSender
    # FIXME: Reload required to re-patch the module with the new fs
    imp.reload(DataSender)

    logs = DataSender.get_install_logs()

    expected_logs = dpkg_logs + apt_logs
    expected_output = [
        {
            'name': log.log_filename,
            'contents': log.contents
        }
        for log in expected_logs
    ]

    assert logs == expected_output
