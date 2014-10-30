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

import os
import drfeedback
import tempfile
from cgi import parse_qs
from urlparse import urljoin

# The directory on the file system where all HTML reports are stored
reports_directory='/tmp/feedback_reports'

def _save_report_(report_id, html_data, directory=reports_directory):
    # Saves the HTML report file on the local filesystem
    filename='feedback-%s.html' % report_id

    try:
        assert (os.path.exists(directory))
        abs_filename=os.path.join(directory, filename)
        htmlfile=open(abs_filename, 'w')
        htmlfile.write(html_data)
        htmlfile.close()
        return filename
    except:
        raise


def _dump_environment_(environment):
    # Just for debugging purposes
    for key in environment:
        print '%s=%s' % (key, environment[key])


def _get_hosturl_(environment):
    # Construct and return the full URL that reaches the feedback html files
    hosturl=urljoin('%s://%s' % (environment['wsgi.url_scheme'], environment['HTTP_HOST']), environment['PATH_INFO'])
    return hosturl


def application(environ, start_response):

    debug=False

    # dump the environment to follow possible problems
    # any exceptions raised in this code will be returned as reason 500 to the client
    if debug:
        _dump_environment_(environ)

    # the environment variable CONTENT_LENGTH may be empty or missing
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except (ValueError):
        raise
 
    # fetch the body from the POST request
    request_body = environ['wsgi.input'].read(request_body_size)

    # extract parameters from the body
    qs = parse_qs(request_body)
    verb=qs['verb'][0]
    report_id=qs['report_id'][0]
    targz=qs['data'][0]
    print 'Received request with verb: %s, report_id: %s, data (tar.gz): %d bytes.' % \
          (verb, report_id, len(targz))

    # Save the targz data in a temporary file
    html_tmpfile=tempfile.NamedTemporaryFile(mode='w+b')
    html_tmpfile.write(qs['data'][0])
    html_tmpfile.flush()

    # Send the tar.gz file for analysis
    report_html=drfeedback.analyze(html_tmpfile.name)

    # closing the tempfile to efectively remove it
    html_tmpfile.close()

    # Save the report in the local filesystem to be served via nginx
    report_file=_save_report_(report_id, report_html)
    assert (report_file)

    # Send the results to the client
    start_response('200 OK', [('Content-Type', 'text/html')])
    ok_message='Feedback request processed successfully: id=%s url=%s' % \
                (report_id, urljoin (_get_hosturl_(environ), report_file))

    print ok_message
    return [ok_message]
