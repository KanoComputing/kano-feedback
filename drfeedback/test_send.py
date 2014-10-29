#!/usr/bin/python
#
# Test the Feedback report tool as a web service.
#

import sys
import requests

if __name__ == '__main__':

    rc = 0

    if len(sys.argv) < 2:
        print 'I need a tar.gz file to send to the web service'
        rc=-1
    else:
        targz=open(sys.argv[1]).read()
        res=requests.post(url='http://localhost:9000', data=targz)
        print 'STATUS_CODE:', res.status_code
        print 'DATA:\n', res.text
        rc=0

    sys.exit(rc)
