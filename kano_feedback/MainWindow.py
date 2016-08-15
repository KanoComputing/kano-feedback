#!/usr/bin/env python

# MainWindow.py
#
# Copyright (C) 2014, 2015 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
# Base class for the Feedback windows.
#

import sys
from gi.repository import Gtk, Gdk, GObject
import threading

GObject.threads_init()

from kano.gtk3.application_window import ApplicationWindow

from kano.utils import run_cmd
from kano_world.functions import is_registered
from kano.network import is_internet
from kano.gtk3.kano_dialog import KanoDialog
# implicit imports
from kano.gtk3.cursor import attach_cursor_events
from kano.gtk3.top_bar import TopBar
from DataSender import (send_data, take_screenshot, copy_screenshot, delete_tmp_dir,
                        create_tmp_dir, SCREENSHOT_NAME, SCREENSHOT_PATH, delete_screenshot)
from kano.gtk3.buttons import KanoButton
from kano.gtk3.scrolled_window import ScrolledWindow
from kano_feedback import Media


class MainWindow(ApplicationWindow):
    CLOSE_FEEDBACK = 0
    KEEP_OPEN = 1
    LAUNCH_WIFI = 2
    WIDTH = 400

    def __init__(self, subject):
        self.subject = subject
        self.bug_report = None

    def send_feedback(self, button=None, event=None, body_title=None):
        '''
        Sends all the information
        Shows a dialogue when Report mode
        Runs a thread for the spinner button and mouse
        '''
        if not hasattr(event, 'keyval') or event.keyval == Gdk.KEY_Return:

            self.check_login()
            if not is_registered():
                self.after_feedback_sent(completed=False)
                return

            if self.bug_report:
                title = _("Important")
                description = (
                    _("Your feedback will include debugging information.\n" +\
                      "Do you want to continue?")
                )
                kdialog = KanoDialog(
                    title, description,
                    {
                        _("CANCEL"):
                        {
                            "return_value": 1
                        },
                        _("OK"):
                        {
                            "return_value": 0
                        }
                    },
                    parent_window=self
                )
                rc = kdialog.run()
                if rc != 0:
                    # Enable button and refresh
                    button.set_sensitive(True)
                    Gtk.main_iteration()
                    return

            self.set_cursor_to_watch()
            self._send_button.start_spinner()
            self._send_button.set_sensitive(False)
            self._text.set_sensitive(False)

            def lengthy_process():
                button_dict = {_("OK"): {"return_value": self.CLOSE_FEEDBACK}}

                if not is_internet():
                    title = _("No internet connection")
                    description = _("Configure your connection")
                    button_dict = {_("OK"): {"return_value": self.LAUNCH_WIFI}}
                else:
                    success, error = self.send_user_info(body_title=body_title)
                    if success:
                        title = _("Info")
                        description = _("Feedback sent correctly")
                        button_dict = \
                            {
                                _("OK"):
                                {
                                    "return_value": self.CLOSE_FEEDBACK
                                }
                            }
                    else:
                        title = _("Info")
                        description = _("Something went wrong, error: {}").format(error)
                        button_dict = \
                            {
                                _("CLOSE FEEDBACK"):
                                {
                                    "return_value": self.CLOSE_FEEDBACK,
                                    "color": "red"
                                },
                                _("TRY AGAIN"):
                                {
                                    "return_value": self.KEEP_OPEN,
                                    "color": "green"
                                }
                            }

                def done(title, description, button_dict):
                    self.set_cursor_to_normal()
                    self._send_button.stop_spinner()
                    self._send_button.set_sensitive(True)
                    self._text.set_sensitive(True)

                    # If the user decides to launch the wifi config,
                    # the window needs to be able to go below kano-settings
                    self.set_keep_above(False)

                    kdialog = KanoDialog(title, description, button_dict,
                                         parent_window=self)
                    kdialog.dialog.set_keep_above(False)
                    response = kdialog.run()

                    if response == self.LAUNCH_WIFI:
                        run_cmd('sudo /usr/bin/kano-settings 12')
                        self.after_feedback_sent(completed=False)
                    elif response == self.CLOSE_FEEDBACK:
                        self.after_feedback_sent(completed=True)

                GObject.idle_add(done, title, description, button_dict)

            thread = threading.Thread(target=lengthy_process)
            thread.start()

    def after_feedback_sent(self, completed):
        '''
        By default we exit the window when Feedback has been sent
        '''
        sys.exit(0)

    def set_cursor_to_watch(self):
        '''
        Sets mouse cursor to hourglass state
        '''
        watch_cursor = Gdk.Cursor(Gdk.CursorType.WATCH)
        self.get_window().set_cursor(watch_cursor)
        self._text.get_window(Gtk.TextWindowType.TEXT).set_cursor(watch_cursor)
        self._text.get_window(Gtk.TextWindowType.WIDGET).set_cursor(watch_cursor)

    def set_cursor_to_normal(self):
        '''
        Sets mouse cursor to pointer state
        '''
        self.get_window().set_cursor(None)
        self._text.get_window(Gtk.TextWindowType.TEXT).set_cursor(None)
        self._text.get_window(Gtk.TextWindowType.WIDGET).set_cursor(None)

    def send_user_info(self, body_title=None):
        '''
        Send all the information to our servers
        '''
        # Text from Entry - the subject of the email
        if hasattr(self, "entry"):
            subject = self.entry.get_text()
        else:
            subject = self.subject

        # Main body of the text
        textbuffer = self._text.get_buffer()
        startiter, enditer = textbuffer.get_bounds()
        text = textbuffer.get_text(startiter, enditer, True)

        # Body title is used for desktop feedback
        # to contain the Prompt suggestion text
        if body_title:
            text = 'Body Title: %s\n\n%s' % (body_title, text)

        success, error = send_data(text, self.bug_report, subject)

        return success, error

    def open_help(self, button=None, event=None):
        '''
        Opens the help app
        '''
        run_cmd("/usr/bin/kano-help-launcher")

    def clear_buffer(self, textbuffer, textiter, text, length):
        '''
        Clears a text buffer
        '''
        self._text.get_style_context().add_class("active")

        start = textbuffer.get_start_iter()
        textbuffer.delete(start, textiter)
        textbuffer.disconnect(self._clear_buffer_handler_id)

        self._send_button.set_sensitive(True)

    def iconify(self):
        '''
        Minimises the window
        '''
        self.hide()

    def deiconify(self):
        '''
        Restores the window
        '''
        self.show_all()

    def check_login(self):
        '''
        Check if user is registered
        If not, then launch kano-login
        '''
        if not is_registered():
            # Make sure the login dialog goes on top
            self.set_keep_above(False)
            self.set_keep_below(True)
            self.show_all()
            _, _, rc = run_cmd('kano-login 3')
            self.set_keep_below(False)
            self.set_keep_above(True)
            self.show_all()
