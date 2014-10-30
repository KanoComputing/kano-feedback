#!/usr/bin/python
#
# Test the Feedback report tool as a web service.
# It will send a tar.gz to the server and return you the URL to browse it
#
# You need the "python-requests" package
# and a tar.gz file from kano feedback.
#

import sys
import requests

if __name__ == '__main__':

    payload = {}
    rc = 0

    if len(sys.argv) < 3:
        print 'Syntax: send_report <hostname> <tar.gz file>'
        sys.exit(1)
    else:
        hosturl=sys.argv[1]
        tarfilename=sys.argv[2]

    # open the tar.gz file and pack it in the payload
    ftar=open(tarfilename, 'rb')
        
    # read the tar.gz file and prepare the payload object
    payload['verb']='report'
    payload['report_id']='12345'
    payload['data']=ftar.read()
    ftar.close()

    # send the request
    print 'sending request to:', hosturl
    response=requests.post(url=hosturl, data=payload)

    print 'STATUS_CODE:', response.status_code
    print 'DATA:', response.text
    sys.exit(0)
