#
# apt_sources.py
#
# Copyright (C) 2018 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#
# Test fixtures to simulate apt sources files
#


import os
import math
import random
import string
import pytest


#
# Generate the set of all subsets
#
# Special thanks to:
#     https://stackoverflow.com/questions/1482308/how-to-get-all-subsets-of-a-set-powerset#answer-1482359
#
def powerset(lst):
    return reduce(
        lambda result, x: result + [subset + [x] for subset in result],
        lst,
        [[]]
    )


def random_string(length):
    char_selection = string.letters + ' \n'

    # random.sample fails if the length required is greater than the population
    factor = int(math.ceil(length / len(char_selection)))
    char_selection *= factor * 3

    return ''.join(
        random.sample(char_selection, length)
    )


def random_file():
    return random_string(random.randint(100, 200))


class AptSrcFile(object):
    def __init__(self, filepath, contents):
        print contents
        self.filepath = filepath
        self.contents = contents

    def __repr__(self):
        return 'AptSrcFile({})'.format(self.filepath)

    def __gt__(self, other):
        return self.filepath > other.filepath


APT_DIR = '/etc/apt'
APT_SRC_DIR = os.path.join(APT_DIR, 'sources.list.d')

APT_SRC_FILES = [
    AptSrcFile(os.path.join(APT_DIR, 'sources.list'), random_file()),
    AptSrcFile(os.path.join(APT_SRC_DIR, 'kano.list'), random_file()),
    AptSrcFile(os.path.join(APT_SRC_DIR, 'collabora.list'), random_file()),
]


@pytest.fixture(scope='function', params=powerset(APT_SRC_FILES))
def apt_sources(fs, request):
    sources = sorted(request.param)

    for source in sources:
        fs.create_file(
            source.filepath,
            contents=source.contents
        )

    return sources
