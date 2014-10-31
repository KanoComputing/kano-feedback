== DrFeedback

A tool to read a tar.gz file from a Feedback email and report a useful HTML document with diagnose information.

=== Local, command line usage:

```
$ python drfeedback.py <tar.gz filename> [full]
```

This will give you the HTML document to stdout.

=== Web service installation

To deploy the web service, on the server you do:

 $ sudo apt-get install gunicorn

Place the "drfeeback" directory somewhere on your server, then edit /etc/gunicorn/*

TODO: complete this part

=== Local web service testing

Make sure you have write permissions to the directory ```reports_directory``` defined in wsgi_main.py.
On one terminal you start the server like this:

 $ gunicorn -b 127.0.0.1:9000 wsgi_main

On another terminal you send a report request like this:

 $ python send_report.py http://localhost:9000 <tar.gz filename>

The HTML document will be placed in the ```reports_directory```.

=== Remote server usage

On a remote system make sure you have the latest python requests package:

 $ sudo pip install requests

Locate the local tar.gz file to send to the server, and do:

 $ python send_report.py http://dev.kano.me/feedback <tar.gz filename> <username> <password>

The URL to the HTML document will be presented with the response.
