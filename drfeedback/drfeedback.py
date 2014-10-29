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

def analyze(tarfilename, full_dump=False):

    # Open the tar.gz file
    try:
        tar = tarfile.open(tarfilename, mode='r')
    except IOError:
        print 'Error opening feedback tarfile', tarfilename
        return None

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

            # send data to inpector to analyze
            # and send results to the presentation layer
            i.inspect(logdata)

            if not full_dump:
                logdata=None

            html_report.add_report(i, logdata)

        except Exception as e:
            print 'Warning: Could not inspect data for logfile %s' % logfile
            traceback.print_exc(file=sys.stdout)
            pass

    # complete the report and hand it over
    html_report.wrap_it_up()
    hmtl_document=html_report.get_html()
    return hmtl_document()


if __name__ == '__main__':

    full_dump=False

    if len(sys.argv) < 2:
        print 'Doctor Feedback - Analyze feedback tar.gz files from Kano Kits'
        print 'Syntax : python drfeedback.py <feedback.tar.gz file> [full]'
        print 'the "full" switch will include the log files along with the summary report.'
        sys.exit(1)
    else:
        tarfilename=sys.argv[1]

    if len(sys.argv) > 2 and sys.argv[2] == 'full':
        full_dump=True

    print analyze(tarfilename, full_dump)
    sys.exit(0)
