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

from kano_feedback.UIElements import TopBar
from DataSender import send_data
from kano.utils import run_cmd
from kano_feedback import Media


class MainWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title='Kano Feedback')

        screen = Gdk.Screen.get_default()
        self._win_width = 500
        self._win_height = int(screen.get_height() * 0.35)

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
        self._text = Gtk.TextView()
        self._text.set_editable(True)
        self._textbuffer = self._text.get_buffer()
        self._textbuffer.set_text("Type your feedback here!")
        scrolledwindow.add(self._text)
        self._clear_buffer_handler_id = self._textbuffer.connect("insert-text", self.clear_buffer)

        # Very hacky way to get a border: create a grey event box which is a little bigger than the widget below
        padding_box = Gtk.Alignment()
        padding_box.set_padding(3, 3, 3, 3)
        padding_box.add(scrolledwindow)
        border = Gtk.EventBox()
        border.get_style_context().add_class("grey")
        border.add(padding_box)

        # This is the "actual" padding
        padding_box2 = Gtk.Alignment()
        padding_box2.set_padding(20, 20, 20, 20)
        padding_box2.add(border)
        self._grid.attach(padding_box2, 0, 1, 1, 1)

        # Create check box
        self._bug_check = Gtk.CheckButton()
        check_label = Gtk.Label("Reporting a bug? Check this to send full details")
        self._bug_check.add(check_label)
        self._bug_check.set_can_focus(False)

        # Create send button
        send_button = Gtk.Button("SEND")
        send_button.get_style_context().add_class("green_button")
        send_button.connect("button_press_event", self.send_feedback)

        # Create grey box to put checkbox and button in
        bottom_box = Gtk.Box()
        bottom_box.pack_start(self._bug_check, False, False, 10)
        bottom_box.pack_end(send_button, False, False, 10)

        bottom_align = Gtk.Alignment(xalign=0.5, yalign=0.5)
        bottom_align.set_padding(10, 10, 10, 10)
        bottom_align.add(bottom_box)

        bottom_background = Gtk.EventBox()
        bottom_background.get_style_context().add_class("grey")
        bottom_background.add(bottom_align)

        self._grid.attach(bottom_background, 0, 2, 1, 1)
        #self._grid.attach(send_button_align, 0, 3, 1, 1)

        self._grid.set_row_spacing(0)
        self.add(self._grid)

    def send_feedback(self, button=None, event=None):
        # Disable button and refresh
        button.set_sensitive(False)
        Gtk.main_iteration()

        fullinfo = self._bug_check.get_active()
        if fullinfo:
            msg = "You are about to send sensitive data. \nDo you want to continue?"
            _, _, rc = run_cmd('zenity --question --text "{}"'.format(msg))
            if rc != 0:
                sys.exit()
        textbuffer = self._text.get_buffer()
        startiter, enditer = textbuffer.get_bounds()
        text = textbuffer.get_text(startiter, enditer, True)
        success, error = send_data(text, fullinfo)
        if success:
            msg = "Feedback sent correctly"
        else:
            msg = "Something went wrong, error: {}".format(error)
        run_cmd('zenity --info --text "{}"'.format(msg))
        sys.exit()

    def clear_buffer(self, textbuffer, textiter, text, length):
        self._text.get_style_context().add_class("active")
        textbuffer.set_text("")
        textbuffer.disconnect(self._clear_buffer_handler_id)

