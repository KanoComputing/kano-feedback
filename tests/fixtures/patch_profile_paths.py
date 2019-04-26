#
# patch_profile_paths.py
#
# Copyright (C) 2019 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#
# Test fixture to patch silly code in kano-profile.
# Remove this once that is fixed.
#


import pytest


@pytest.fixture(scope='function')
def fix_profile(fs):
    # TODO: kano-profile/*/paths.py throws an exception when it cannot find
    # a project dir. This creates problems when using other fixtures with
    # pyfakefs since the import below will be affected. Create the dir here
    # next to the import from kano-toolset to avoid the exception.
    import os
    fs.create_dir('/usr/share/kano-profile/rules/')
    fs.create_dir('/usr/bin')
    fs.create_dir('/usr/share/kano-desktop/Legal/')
    fs.create_dir('/usr/share/kano-profile/media/')
    fs.create_dir(os.path.expanduser('~/.kanoprofile/tracker'))
    fs.create_file(os.path.expanduser('~/.kanoprofile/tracker/token'))
