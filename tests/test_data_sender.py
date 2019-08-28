#
# test_data_sender.py
#
# Copyright (C) 2018-2019 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#
# Tests that the data is correctly collected and sent
#


import imp
import json
from tests.fixtures.helpers import random_file


class ExpectedFile(object):
    def __init__(self, filename, contents, fn=''):
        self.filename = filename
        self.contents = contents
        self.fn = fn

    def mock_fn(self, *args, **kwargs):
        return self.contents


TEST_TITLE = 'Some test title'
TEST_DESC = 'Some test decription'


EXPECTED_FILES = [
    ExpectedFile(filename='kanux_version.txt', fn='get_version', contents=random_file()),
    ExpectedFile(filename='kanux_stamp.txt', fn='get_stamp', contents=random_file()),
    ExpectedFile(filename='process.txt', fn='get_processes', contents=random_file()),
    ExpectedFile(filename='process-tree.txt', fn='get_process_tree', contents=random_file()),
    ExpectedFile(filename='packages.txt', fn='get_packages', contents=random_file()),
    ExpectedFile(filename='dmesg.txt', fn='get_dmesg', contents=random_file()),
    ExpectedFile(filename='syslog.txt', fn='get_syslog', contents=random_file()),
    # ExpectedFile(filename='cmdline.txt', fn='read_file_fn', contents=random_file()),
    # ExpectedFile(filename='config.txt', fn='read_file_fn', contents=random_file()),
    ExpectedFile(filename='wifi-info.txt', fn='get_wifi_info', contents=random_file()),
    ExpectedFile(filename='usbdevices.txt', fn='get_usb_devices', contents=random_file()),
    ExpectedFile(filename='app-logs.txt', fn='get_app_logs_raw', contents=random_file()),
    ExpectedFile(filename='app-logs-json.txt', fn='get_app_logs_json', contents=random_file()),
    ExpectedFile(filename='hdmi-info.txt', fn='get_hdmi_info', contents=random_file()),
    ExpectedFile(filename='edid.dat', fn='get_edid', contents=random_file()),
    ExpectedFile(filename='screen-log.txt', fn='get_screen_log', contents=random_file()),
    ExpectedFile(filename='xorg-log.txt', fn='get_xorg_log', contents=random_file()),
    ExpectedFile(filename='cpu-info.txt', fn='get_cpu_info', contents=random_file()),
    ExpectedFile(filename='mem-stats.txt', fn='get_mem_stats', contents=random_file()),
    ExpectedFile(filename='lsof.txt', fn='get_lsof', contents=random_file()),
    ExpectedFile(filename='content-objects.txt', fn='get_co_list', contents=random_file()),
    ExpectedFile(filename='disk-space.txt', fn='get_disk_space', contents=random_file()),
    ExpectedFile(filename='lsblk.txt', fn='get_lsblk', contents=random_file()),
    ExpectedFile(filename='sources-list.txt', fn='get_sources_list', contents=random_file()),
    ExpectedFile(filename='metadata.json', contents=json.dumps({'title': TEST_TITLE, 'description': TEST_DESC})),
]


def test_send_data(mocker, requests_mock, console_mode, monkeypatch, stub):
    # Stub out some kano_world.functions`
    stub.apply({
        'kano.notifications.display_generic_notification': '[func]',
        'kano_world.functions': {
            'get_email': lambda: 'test@kano.me',
            'get_mixed_username': lambda: 'testuser',
        },
    })

    # Fake the API, in the future we might want to actually test the data
    # sent
    post_mock = requests_mock.post(
        'https://worldapi.kes.kano.me/feedback',
        json={'result': 200}
    )

    # Stub the get_metadata_archive()
    import io

    title = 'test title'
    desc = 'test description'
    archive_data = io.BytesIO(b'Fake metadata archive file')

    get_archive_stub = mocker.stub()
    get_archive_stub.side_effect = lambda *args, **kwargs: archive_data

    import kano_feedback.DataSender as DataSender
    monkeypatch.setattr(DataSender, 'get_metadata_archive', get_archive_stub)

    # Call function under test
    DataSender.send_data(desc, True, subject=title)

    # Verify
    assert len(post_mock.request_history) == 1

    assert get_archive_stub.call_count == 1
    get_archive_stub.assert_called_with(title=title, desc=desc)


def test_get_metadata_archive(fs, monkeypatch, console_mode):
    fs.create_dir('/var/tmp/')

    import kano_feedback.DataSender as DataSender
    fs.create_dir(DataSender.TMP_DIR)
    imp.reload(DataSender)

    for expected_f in EXPECTED_FILES:
        if hasattr(DataSender, expected_f.fn):
            monkeypatch.setattr(
                DataSender, expected_f.fn, expected_f.mock_fn
            )

    # Call function under test
    archive = DataSender.get_metadata_archive(title=TEST_TITLE, desc=TEST_DESC)

    # Verify
    import tarfile
    import os

    assert os.path.exists(os.path.join(
        os.path.expanduser('~'), '.kano-feedback', 'bug_report.tar.gz'
    ))

    extraction_path = '/testdata'
    fs.create_dir(extraction_path)

    with tarfile.open('archive', mode='r', fileobj=archive) as archive_f:
        archive_f.extractall(path=extraction_path)
        assert sorted([f.filename for f in EXPECTED_FILES]) \
            == sorted(os.listdir(extraction_path))

        for expected_f in EXPECTED_FILES:
            filepath = os.path.join(extraction_path, expected_f.filename)
            with open(filepath, 'r') as archive_f:
                assert expected_f.contents == archive_f.read()


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
