#
# patch_toolset_paths.py
#
# Copyright (C) 2019 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#
# Test fixture to patch silly code in kano-toolset.
# Remove this once that is fixed.
#


import pytest


@pytest.fixture(scope='function')
def fix_toolset(fs):
    # TODO: kano-toolset/kano/paths.py throws an exception when it cannot find
    # a project dir. This creates problems when using other fixtures with
    # pyfakefs since the import below will be affected. Create the dir here
    # next to the import from kano-toolset to avoid the exception.
    fs.create_dir('/usr/share/kano/media')
