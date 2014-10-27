#!/usr/bin/python
#
#  Module that receives reports from Kano Feedback inspectors, and presents them in a HTML document
#  For making life easier, we are generating the HTML document using the compact versatile "markup.py" module
#
#   http://markup.sourceforge.net/
#

import feedback_inspectors
import markup
import base64

#
# Class that implements the HTML document for DrFeeback complete report
#
class FeedbackPresentation:
    def __init__(self, filename, title=None, css=None, header=None, footer=None, h1_title=None):
        '''
        Build and html document called "page" where we can build up html information areas
        '''
        self.info=[]
        self.warn=[]
        self.error=[]
        self.logs=[]

        self.page=markup.page()
        self.page.init(title=title, css=css, header=header, footer=footer)
        if h1_title:
            self.page.h1(h1_title)

    def add_report(self, inspector, logdata):
        '''
        Collect information and logfile sections from this inspector
        '''
        if len(inspector.get_info()): self.info.append(inspector.get_info())
        if len(inspector.get_warn()): self.warn.append(inspector.get_warn())
        if len(inspector.get_error()): self.error.append(inspector.get_error())

        if logdata:
            # FIXME: Find a more elegant way to detect a screenshot file
            if logdata[0] == '\x89PNG\r\n':
                format='image'
            else:
                format='text'

            self.logs.append({ 'logfile' : inspector.logfile, 'logdata' : logdata, 'format' : format })

    def wrap_it_up(self):
        '''
        Uniformly join all the information and logfiles in a single document in 2 sections
        '''
        self.page.h2('Summary section')
        self.page.h3('Information')

        for entry in self.info:
            self.page.ul(class_='inspector-information')
            self.page.li(entry, class_='info-entry')
            self.page.ul.close()

        self.page.h3('Warning')
        for entry in self.warn:
            self.page.ul(class_='inspector-warning')
            self.page.li(entry, class_='warn-entry')
            self.page.ul.close()

        self.page.h3('Error')
        for entry in self.error:
            self.page.ul(class_='inspector-error')
            self.page.li(entry, class_='error-entry')
            self.page.ul.close()

        self.page.h2('Logfile section')
        for log in self.logs:
            self.page.h3('Dump logfile: %s' % log['logfile'])
            if log['format'] == 'image':
                img64=base64.b64encode(''.join(log['logdata']))
                self.page.img(src='data:image/png;base64,%s' % img64)
                pass
            else:
                self.page.pre(''.join(log['logdata']), class_='logfile')

    def get_html(self):
        return self.page
