#!/usr/bin/python
#
# drfeedback.py - Doctor Feedback
#
# This script takes a Kano Feedback tar.gz data file
# inspects each of the system logs and reports information
# in a more human readable format.
#

import os
import sys
import tarfile
import traceback

from feedback_inspectors import *

if __name__ == '__main__':

    full_dump=False

    if len(sys.argv) < 2:
        print 'Doctor Feedback'
        print 'Syntax : python drfeedback.py <feedback.tar.gz file> [full]'
        print 'the "full" switch will also emit all the log files in sequence to stdout'
        sys.exit(1)
    else:
        tarfilename=sys.argv[1]

    if len(sys.argv) > 2 and sys.argv[2] == 'full':
        full_dump=True

    # Open the tar.gz file
    try:
        tar = tarfile.open(tarfilename)
    except IOError:
        print 'Error opening feedback tarfile', tarfilename
        sys.exit(1)

    # inspect the tarfile without actually extracting anything
    for member in tar.getmembers():

        try:
            # find out each logfile to determine the inspector
            logfile=member.name
            print '>>> report for logfile:', logfile

            # we extract the logfile contents in-process
            logdata=tar.extractfile(member).read()

            # instantiate the inspector that understands this logfile
            # remove possibly appended paths in the filename
            i=inspectors[os.path.basename(member.name)]()

            # and print what the inspector has to warn us about
            report = i.inspect(logfile, logdata)
            for l in i.report_info():
                print 'info:', l
            for l in i.report_warn():
                print 'warn:', l
            for l in i.report_error():
                print 'error:', l

            if full_dump:
                print '>>> full dump logdata follows:'
                print logdata

        except Exception as e:
            print 'Warning: Could not inspect data for logfile %s' % logfile
            traceback.print_exc(file=sys.stdout)
            pass

    sys.exit(0)
