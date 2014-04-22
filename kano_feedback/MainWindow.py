#!/usr/bin/env python

# MainWindow.py
#
# Copyright (C) 2014 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
# The MainWindow class
#

import sys
from gi.repository import Gtk, Gdk

from kano_extras.UIElements import TopBar
from DataSender import send_data
from kano.utils import run_cmd
from kano_feedback import Media


class MainWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title='Kano Feedback')

        screen = Gdk.Screen.get_default()
        self._win_width = 500
        self._win_height = int(screen.get_height() * 0.5)

        self.set_decorated(False)
        self.set_resizable(False)
        self.set_size_request(self._win_width, self._win_height)

        self.set_position(Gtk.WindowPosition.CENTER)

        self.connect('delete-event', Gtk.main_quit)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_path(Media.media_dir() + 'css/style.css')
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider,
                                              Gtk.STYLE_PROVIDER_PRIORITY_USER)

        self._grid = Gtk.Grid()

        # Create top bar
        self._top_bar = TopBar()
        self._grid.attach(self._top_bar, 0, 0, 1, 1)

        # Create Text view
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)
        self._grid.attach(scrolledwindow, 0, 1, 1, 1)
        self._text = Gtk.TextView()
        self._text.set_editable(True)
        self._textbuffer = self._text.get_buffer()
        self._textbuffer.set_text("Let us know your feeback!")
        scrolledwindow.add(self._text)

        # Create send button
        send_button = Gtk.EventBox()
        send_button.get_style_context().add_class("apply_changes_button")
        send_button.get_style_context().add_class("green")
        send_label = Gtk.Label("SEND")
        send_label.get_style_context().add_class("apply_changes_text")
        send_button.add(send_label)
        send_button.set_size_request(200, 44)
        send_button.connect("button_press_event", self.send_feedback)
        self._grid.attach(send_button, 0, 2, 1, 1)

        self._grid.set_row_spacing(0)
        self.add(self._grid)

    def send_feedback(self, event=None, button=None):

        msg = "You are about to send sensitive data. \nDo you want to continue?"
        _, _, rc = run_cmd('zenity --question --text "{}"'.format(msg))
        if rc != 0:
            sys.exit()

        textbuffer = self._text.get_buffer()
        startiter, enditer = textbuffer.get_bounds()
        text = textbuffer.get_text(startiter, enditer, True)
        success = send_data(text, False)
        if success:
            msg = "Feedback sent correctly"
        else:
            msg = "Something went wrong"
        run_cmd('zenity --info --text "{}"'.format(msg))
