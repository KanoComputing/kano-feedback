#!/usr/bin/env python

# MainWindow.py
#
# Copyright (C) 2014 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
# The MainWindow class
#

import sys
from gi.repository import Gtk, Gdk, GObject
import threading

GObject.threads_init()

from kano.gtk3.top_bar import TopBar
from DataSender import send_data, take_screenshot
from kano.utils import run_cmd
from kano.network import is_internet
from kano.gtk3.kano_dialog import KanoDialog
from kano.gtk3 import cursor
from kano.gtk3.buttons import KanoButton, OrangeButton
from kano.gtk3.scrolled_window import ScrolledWindow
from kano.gtk3.application_window import ApplicationWindow
from kano_feedback import Media


class MainWindow(ApplicationWindow):
    CLOSE_FEEDBACK = 0
    KEEP_OPEN = 1
    LAUNCH_WIFI = 2

    def __init__(self, bug_report=False):
        self.bug_report = bug_report
        if self.bug_report:
            self.report_window()
        else:
            self.contact_window()

    def contact_window(self):
        ApplicationWindow.__init__(self, 'Contact Us', 500, 0.35)

        screen = Gdk.Screen.get_default()
        specific_provider = Gtk.CssProvider()
        specific_provider.load_from_path(Media.media_dir() + 'css/style.css')
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, specific_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        self.set_icon_name("feedback")
        # Make sure this window is always above
        self.set_keep_above(True)

        self._grid = Gtk.Grid()

        # Create top bar
        self._top_bar = TopBar(title="Contact Us", window_width=500, has_buttons=False)
        self._top_bar.set_close_callback(Gtk.main_quit)

        self._grid.attach(self._top_bar, 0, 0, 1, 1)

        # Create Text view
        scrolledwindow = ScrolledWindow()
        scrolledwindow.set_hexpand(False)
        scrolledwindow.set_vexpand(True)
        self._text = Gtk.TextView()
        self._text.set_editable(True)
        self._textbuffer = self._text.get_buffer()
        self._textbuffer.set_text("Type your feedback here!")
        scrolledwindow.add(self._text)
        scrolledwindow.set_margin_left(2)
        scrolledwindow.set_margin_right(2)
        scrolledwindow.set_margin_top(2)
        scrolledwindow.set_margin_bottom(2)

        self._clear_buffer_handler_id = self._textbuffer.connect("insert-text", self.clear_buffer)

        # Very hacky way to get a border: create a grey event box which is a little bigger than the widget below
        border = Gtk.EventBox()
        border.get_style_context().add_class("grey")
        border.add(scrolledwindow)
        self._grid.attach(border, 0, 2, 1, 1)
        border.set_margin_left(20)
        border.set_margin_right(20)
        border.set_margin_top(10)
        border.set_margin_bottom(20)

        # Create send button
        self._send_button = KanoButton("SEND")
        self._send_button.set_sensitive(False)
        self._send_button.connect("button_press_event", self.send_feedback)

        bottom_align = Gtk.Alignment(xalign=0.5, yalign=0.5)
        bottom_align.set_padding(10, 10, 10, 10)
        bottom_align.add(self._send_button)

        bottom_background = Gtk.EventBox()
        bottom_background.get_style_context().add_class("grey")
        bottom_background.add(bottom_align)

        self._grid.attach(bottom_background, 0, 3, 1, 1)

        # FAQ button
        self._faq_button = OrangeButton("Check out our FAQ")
        self._faq_button.set_sensitive(True)
        self._faq_button.connect("button_release_event", self.open_help)
        cursor.attach_cursor_events(self._faq_button)
        self._grid.attach(self._faq_button, 0, 4, 1, 1)

        self._grid.set_row_spacing(0)
        self.set_main_widget(self._grid)

        # kano-profile stat collection
        try:
            from kano_profile.badges import increment_app_state_variable_with_dialog
            increment_app_state_variable_with_dialog('kano-feedback', 'starts', 1)
        except Exception:
            pass

    def report_window(self):
        ApplicationWindow.__init__(self, 'Report a bug', 500, 0.35)

        screen = Gdk.Screen.get_default()
        specific_provider = Gtk.CssProvider()
        specific_provider.load_from_path(Media.media_dir() + 'css/style.css')
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, specific_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        self.set_icon_name("feedback")
        # Make sure this window is always above
        self.set_keep_above(True)

        self._grid = Gtk.Grid()

        # Create top bar
        self._top_bar = TopBar(title="Report a bug", window_width=500, has_buttons=False)
        self._top_bar.set_close_callback(Gtk.main_quit)

        self._grid.attach(self._top_bar, 0, 0, 1, 1)

        self.entry = Gtk.Entry()
        self.entry.props.placeholder_text = "Add subject (optional)"
        self.entry.set_margin_left(20)
        self.entry.set_margin_right(20)
        self.entry.set_margin_top(20)
        self.entry.set_margin_bottom(10)
        self._grid.attach(self.entry, 0, 1, 1, 1)

        # Create Text view
        scrolledwindow = ScrolledWindow()
        scrolledwindow.set_hexpand(False)
        scrolledwindow.set_vexpand(True)
        self._text = Gtk.TextView()
        self._text.set_editable(True)
        self._textbuffer = self._text.get_buffer()
        self._textbuffer.set_text("Type your problem here!")
        scrolledwindow.add(self._text)
        scrolledwindow.set_margin_left(2)
        scrolledwindow.set_margin_right(2)
        scrolledwindow.set_margin_top(2)
        scrolledwindow.set_margin_bottom(2)

        self._clear_buffer_handler_id = self._textbuffer.connect("insert-text", self.clear_buffer)

        # Very hacky way to get a border: create a grey event box which is a little bigger than the widget below
        border = Gtk.EventBox()
        border.get_style_context().add_class("grey")
        border.add(scrolledwindow)
        self._grid.attach(border, 0, 2, 1, 1)
        border.set_margin_left(20)
        border.set_margin_right(20)
        border.set_margin_top(10)
        border.set_margin_bottom(20)

        # Create take screenshot button
        self._screenshot_button = KanoButton("SCREENSHOT")
        self._screenshot_button.set_sensitive(True)
        self._screenshot_button.connect("button_press_event", self.screenshot_clicked)

        # Create send button
        self._send_button = KanoButton("SEND")
        self._send_button.set_sensitive(False)
        self._send_button.connect("button_press_event", self.send_feedback)

        # Create grey box to put the button in
        bottom_box = Gtk.Box()
        bottom_box.pack_end(self._screenshot_button, False, False, 10)
        bottom_box.pack_end(self._send_button, False, False, 10)

        bottom_align = Gtk.Alignment(xalign=0.5, yalign=0.5)
        bottom_align.set_padding(10, 10, 10, 10)
        bottom_align.add(bottom_box)

        bottom_background = Gtk.EventBox()
        bottom_background.get_style_context().add_class("grey")
        bottom_background.add(bottom_align)

        self._grid.attach(bottom_background, 0, 3, 1, 1)

        # FAQ button
        self._faq_button = OrangeButton("Check out our FAQ")
        self._faq_button.set_sensitive(True)
        self._faq_button.connect("button_release_event", self.open_help)
        cursor.attach_cursor_events(self._faq_button)
        self._grid.attach(self._faq_button, 0, 4, 1, 1)

        self._grid.set_row_spacing(0)
        self.set_main_widget(self._grid)

        # kano-profile stat collection
        try:
            from kano_profile.badges import increment_app_state_variable_with_dialog
            increment_app_state_variable_with_dialog('kano-feedback', 'starts', 1)
        except Exception:
            pass

    def send_feedback(self, button=None, event=None):
        if not hasattr(event, 'keyval') or event.keyval == Gdk.KEY_Return:

            if self.bug_report:
                title = "Important"
                description = "Your feedback will include debugging information. \nDo you want to continue?"
                kdialog = KanoDialog(
                    title, description,
                    {
                        "CANCEL":
                        {
                            "return_value": 1
                        },
                        "OK":
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
            self._send_button.set_sensitive(False)
            self._text.set_sensitive(False)

            def lengthy_process():
                button_dict = {"OK": {"return_value": self.CLOSE_FEEDBACK}}

                if not is_internet():
                    title = "No internet connection"
                    description = "Configure your connection"

                    button_dict = {"OK": {"return_value": self.LAUNCH_WIFI}}
                else:
                    success, error = self.send_user_info()

                    if success:
                        title = "Info"
                        description = "Feedback sent correctly"
                        button_dict = \
                            {
                                "OK":
                                {
                                    "return_value": self.CLOSE_FEEDBACK
                                }
                            }
                    else:
                        title = "Info"
                        description = "Something went wrong, error: {}".format(error)
                        button_dict = \
                            {
                                "CLOSE FEEDBACK":
                                {
                                    "return_value": self.CLOSE_FEEDBACK,
                                    "color": "red"
                                },
                                "TRY AGAIN":
                                {
                                    "return_value": self.KEEP_OPEN,
                                    "color": "green"
                                }
                            }

                def done(title, description, button_dict):

                    self.set_cursor_to_normal()
                    self._send_button.set_sensitive(True)
                    self._text.set_sensitive(True)

                    # If the user decides to launch the wifi config,
                    #the window needs to be able to go below kano-settings
                    self.set_keep_above(False)

                    kdialog = KanoDialog(title, description, button_dict, parent_window=self)
                    kdialog.dialog.set_keep_above(False)
                    response = kdialog.run()

                    if response == self.LAUNCH_WIFI:
                        run_cmd('sudo /usr/bin/kano-settings 4')
                    elif response == self.CLOSE_FEEDBACK:
                        sys.exit(0)

                GObject.idle_add(done, title, description, button_dict)

            thread = threading.Thread(target=lengthy_process)
            thread.start()

    def set_cursor_to_watch(self):
        watch_cursor = Gdk.Cursor(Gdk.CursorType.WATCH)
        self.get_window().set_cursor(watch_cursor)
        self._text.get_window(Gtk.TextWindowType.TEXT).set_cursor(watch_cursor)
        self._text.get_window(Gtk.TextWindowType.WIDGET).set_cursor(watch_cursor)

    def set_cursor_to_normal(self):
        self.get_window().set_cursor(None)
        self._text.get_window(Gtk.TextWindowType.TEXT).set_cursor(None)
        self._text.get_window(Gtk.TextWindowType.WIDGET).set_cursor(None)

    def send_user_info(self):
        # Text from Entry - the subject of the email
        subject = self.entry.get_text()

        # Main body of the text
        textbuffer = self._text.get_buffer()
        startiter, enditer = textbuffer.get_bounds()
        text = textbuffer.get_text(startiter, enditer, True)

        success, error = send_data(text, self.bug_report, subject)

        return success, error

    def open_help(self, button=None, event=None):
        run_cmd("/usr/bin/kano-help-launcher")

    def clear_buffer(self, textbuffer, textiter, text, length):
        self._text.get_style_context().add_class("active")

        start = textbuffer.get_start_iter()
        textbuffer.delete(start, textiter)
        textbuffer.disconnect(self._clear_buffer_handler_id)

        self._send_button.set_sensitive(True)

    def screenshot_clicked(self, button=None, event=None):
        # Minimise
        take_screenshot()
        # Maximise
