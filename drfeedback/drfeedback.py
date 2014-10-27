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
from feedback_presentation import FeedbackPresentation


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
        tar = tarfile.open(tarfilename, mode='r')
    except IOError:
        print 'Error opening feedback tarfile', tarfilename
        sys.exit(1)

    # prepare the report
    h1_title='Report for Kano Feedback file %s' % (tarfilename)
    html_report=FeedbackPresentation(filename=tarfilename, title='Doctor Kano Feedback', h1_title=h1_title, footer='Kano Computing 2014')

    # inspect the tarfile without actually extracting anything
    for member in tar.getmembers():
        try:
            # find out each logfile to determine the inspector
            logfile=member.name

            # we extract the logfile contents in-process
            logdata=tar.extractfile(member).readlines()

            # instantiate the inspector that understands this logfile
            # remove possibly appended paths in the filename
            i=inspectors[os.path.basename(member.name)](logfile)

            # and print what the inspector has to warn us about
            i.inspect(logdata)
            html_report.add_report(i, logdata)

        except Exception as e:
            print 'Warning: Could not inspect data for logfile %s' % logfile
            traceback.print_exc(file=sys.stdout)
            pass

    # complete the report and hand it over
    html_report.wrap_it_up()
    print html_report.get_html()

    sys.exit(0)
