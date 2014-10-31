#!/usr/bin/python
#
# Test the Feedback report tool as a web service.
# It will send a tar.gz to the server and return you the URL to browse it
#
# You need the "python-requests" package
# and a tar.gz file from kano feedback.
#

import sys
import os
import requests

if __name__ == '__main__':

    username=password=None
    rc = 0

    if len(sys.argv) < 3:
        print 'Syntax: send_report <hostname> <tar.gz file> [username] [passwor]'
        sys.exit(1)
    else:
        hosturl=sys.argv[1]
        tarfilename=sys.argv[2]

        if len(sys.argv) > 3:
            username=sys.argv[3]
            password=sys.argv[4]

    # read the tar.gz file and prepare the payload object
    form_params= { 'verb' : 'report', 'report_id' : os.path.basename(tarfilename) }

    # attach the tar.gz file
    attachments = [ ('tarfiles', (tarfilename, open(tarfilename, 'rb'), 'application/octet-stream')) ]

    # send the request
    print 'sending request to:', hosturl
    response=requests.post(url=hosturl, data=form_params, files=attachments, auth=(username, password))

    print 'STATUS_CODE:', response.status_code
    print 'DATA:', response.text
    sys.exit(0)
