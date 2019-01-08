#
# helpers.py
#
# Copyright (C) 2019 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#
# Helper functions for tests
#


import math
import random
import string


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


class FakeFile(object):
    def __init__(self, filepath, contents='', log_filename=''):
        self.filepath = filepath
        self.contents = contents if contents else random_file()

        self.log_filename = log_filename if log_filename else filepath

    def __repr__(self):
        return 'FakeFile({})'.format(self.filepath)

    def __gt__(self, other):
        return self.filepath > other.filepath
