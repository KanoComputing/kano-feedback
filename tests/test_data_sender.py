#
# test_data_sender.py
#
# Copyright (C) 2018 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#
# Tests that the data is correctly collected and sent
#


import imp


def test_get_sources_list(console_mode, apt_sources):
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
