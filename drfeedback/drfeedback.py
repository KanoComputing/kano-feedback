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

            # we extract the logfile contents in-process
            logdata=tar.extractfile(member).readlines()

            # instantiate the inspector that understands this logfile
            i=inspectors[member.name]()

            # and print what the inspector has to warn us about
            report = i.inspect(logfile, logdata)
            print '>>> report for logfile:', logfile
            for l in i.report_info():
                print 'info:', l
            for l in i.report_warn():
                print 'warn:', l
            for l in i.report_error():
                print 'error:', l

            if full_dump:
                print '>>> full dump logdata follows:'
                for l in logdata:
                    print l,
                print

        except Exception as e:
            print 'Could not inspect data for logfile %s' % logfile
            traceback.print_exc(file=sys.stdout)
            pass

    sys.exit(0)
