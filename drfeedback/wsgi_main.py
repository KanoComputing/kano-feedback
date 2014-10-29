#!/usr/bin/python
#
#  wsgi_main.py - Provide an entry to Feedback reports via a WSGI interface.
#  This allows for serving reports behind Gunicorn, uWSGI or equivalent.
#
#  If using gunicorn, you can test it like this:
#
#  $ gunicorn -b 127.0.0.1:9000 wsgi_main
#
#  And from another terminal do:
#
#  $ python test_send.py <my_tar_gz file>
#

import drfeedback
import tempfile
from cgi import parse_qs, escape

def application(environ, start_response):

    # the environment variable CONTENT_LENGTH may be empty or missing
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except (ValueError):
        request_body_size = 0

    # fetch the tar.gz from the body and pass it along to the feedback tool
    request_body = environ['wsgi.input'].read(request_body_size)

    html_tmpfile=tempfile.NamedTemporaryFile(mode='w+b')
    html_tmpfile.write(request_body)
    html_tmpfile.flush()

    # Send the tar.gz file for analysis
    data=drfeedback.analyze(html_tmpfile.name)
    html_tmpfile.close()

    # Send the results to the client
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [data]
