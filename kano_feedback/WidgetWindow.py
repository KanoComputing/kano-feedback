#!/usr/bin/env python

# WidgetWindow.py
#
# Copyright (C) 2014 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
# The MainWindow for the Desktop Feedback Widget
#

import sys
from gi.repository import Gtk, Gdk, GObject, GdkPixbuf
import threading
import requests
import json

GObject.threads_init()

from kano.gtk3.top_bar import TopBar

from kano_feedback.DataSender import (send_data, take_screenshot, copy_screenshot, delete_tmp_dir,
                        create_tmp_dir, SCREENSHOT_NAME, SCREENSHOT_PATH, delete_screenshot)

from kano.utils import run_cmd

from kano_world.functions import is_registered
from kano.network import is_internet
from kano.gtk3.kano_dialog import KanoDialog
from kano.gtk3.buttons import KanoButton
from kano.gtk3.scrolled_window import ScrolledWindow
from kano.gtk3.application_window import ApplicationWindow

from kano_feedback import Media


class MainWindow(ApplicationWindow):
    CLOSE_FEEDBACK = 0
    KEEP_OPEN = 1
    LAUNCH_WIFI = 2
    WIDTH = 400
    HEIGHT_COMPACT = 50
    HEIGHT_EXPANDED = 200

    def __init__(self, width=WIDTH, height=HEIGHT_COMPACT):
        # TODO: Fetch rotating prompts dynamically from an external source

        self.prompts_file='/usr/share/kano-feedback/media/widget/prompts.json'
        self.prompts_url='http://dev.kano.me/temp/widget-prompts.json'
        self.prompts=None
        self.current_prompt = 0

        self.rotating_mode=True
        self.in_submit=False
        self.load_prompts()
        self.rotating_prompt_window()

    def load_prompts(self):
        # Periodically fetch a list of prompts from the network, or a local file if not available
        if self.check_internet():
            try:
                r = requests.get(self.prompts_url)
                if r.status_code == 200:
                    prompts = json.loads(r.text)
                self.prompts = sorted(prompts, key=lambda k: k['priority']) 
            except:
                pass

        if not self.prompts:
            try:
                with open (self.prompts_file, 'r') as f:
                    prompts=json.loads(f.read())
                self.prompts = sorted(prompts, key=lambda k: k['priority']) 
            except:
                pass

    def get_next_prompt(self):
        text = 'Click here to send feedback to Kano'
        try:
            text = self.prompts[self.current_prompt]['text']
            if self.current_prompt == len(self.prompts) - 1:
                self.current_prompt = 0
            else:
                self.current_prompt += 1
        except:
            pass

        return text

    def rotating_prompt_window(self):
        ApplicationWindow.__init__(self, 'Report a Problem', self.WIDTH, self.HEIGHT_COMPACT)

        # FIXME: Initially invisible until we position the widget centered on the screen
        self.visible=False

        screen = Gdk.Screen.get_default()
        specific_provider = Gtk.CssProvider()
        specific_provider.load_from_path(Media.media_dir() + 'css/style.css')
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, specific_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        # The widget window has no frame or title bar or borders, and it always sits behind all top level windows
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_keep_above(False)
        self.set_property('skip-taskbar-hint', True)

        self._grid = Gtk.Grid()
        self._grid.set_vexpand(False)
        self._grid.set_hexpand(False)

        # The rotating prompt goes here
        self.rotating_text = Gtk.Label()
        self.rotating_text.set_margin_left(10)
        self.rotating_text.set_margin_right(10)
        self.rotating_text.set_margin_top(10)
        self.rotating_text.set_margin_bottom(10)
        
        # FIXME: how to center the text in the label
        self.rotating_text.set_halign(Gtk.Align.CENTER)
        self.rotating_text.set_text (self.get_next_prompt())

        # When the widget is clicked, it will be expanded or compacted
        self.connect("button_press_event", self.window_clicked)

        self._grid.attach(self.rotating_text, 0, 0, 1, 1)

        # And when the widget loses interactive focus it will shrink back again
        self.connect("focus-out-event", self.focus_out)

        self._grid.set_row_spacing(0)
        self.set_main_widget(self._grid)

    def window_clicked(self, a, b):
        if self.in_submit:
            return
        
        if self.rotating_mode:
            self.expand_window()
        else:
            self.shrink_window()

    def focus_out(self, a, b):
        if not self.in_submit:
            self.shrink_window()
            
    def check_internet(self):
        _, _, rc = run_cmd('/usr/bin/is_internet')
        return (rc == 0)

    def expand_window(self):
        self.rotating_mode=False
        is_internet=self.check_internet()

        if is_internet:
            self.rotating_text.set_text ('Talk to the Kano Team')
        else:
            self.rotating_text.set_text('Please check your internet connection')

        # Wrap the multiline text into a scrollable
        self.scrolledwindow = ScrolledWindow()
        self.scrolledwindow.set_vexpand(False)
        self.scrolledwindow.set_hexpand(False)
        self.scrolledwindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolledwindow.apply_styling_to_widget()
        self.scrolledwindow.set_margin_left(2)
        self.scrolledwindow.set_margin_right(2)
        self.scrolledwindow.set_margin_top(2)
        self.scrolledwindow.set_margin_bottom(2)
        self.scrolledwindow.set_size_request(self.WIDTH, self.HEIGHT_EXPANDED)

        # The text input area: The message to send to Kano
        self.entry = Gtk.TextView()
        self.entry.set_vexpand(False)
        self.entry.set_hexpand(False)
        self.entry.set_margin_left(20)
        self.entry.set_margin_right(20)
        self.entry.set_margin_top(20)
        self.entry.set_margin_bottom(20)
        self.entry.set_size_request(self.WIDTH, self.HEIGHT_EXPANDED)

        self.scrolledwindow.add(self.entry)
        self._grid.attach(self.scrolledwindow, 0, 1, 1, 1)

        # Create a Submit button
        # TODO: If there is no internet do not enable the button, display a message instead
        self._submit_button = KanoButton("Submit", "blue")
        self._submit_button.connect("button_press_event", self.submit_clicked)

        # Disable submit if no network connectivity
        self._submit_button.set_sensitive(is_internet)

        # Create a box that will hold the button
        self.submit_box = Gtk.ButtonBox()
        self.submit_box.set_layout(Gtk.ButtonBoxStyle.CENTER)
        self.submit_box.set_spacing(20)

        # Put the submit button inside the box
        self.submit_box.pack_start(self._submit_button, False, False, 0)
        self.submit_box.set_child_non_homogeneous(self._submit_button, True)
        self.submit_box.set_margin_bottom(20)

        # Add the button box inside the grid
        self._grid.attach(self.submit_box, 0, 2, 1, 1)
        
        self._grid.show_all()

    def shrink_window(self):
        if self.rotating_mode:
            return
        else:
            self.rotating_mode=True

        # Resize the window
        self._grid.set_size_request(self.WIDTH, self.HEIGHT_COMPACT)

        # Remove unnecessary widgets from the grid and display current prompt
        self._grid.remove(self.scrolledwindow)
        self._grid.remove(self.submit_box)
        self.rotating_text.set_text (self.get_next_prompt())
        self._grid.show_all()

    def submit_clicked(self, window, event):
        self.in_submit=True
        dialog_buttons = { 'CANCEL' : { 'return value' : 1 }, 'OK' : { 'return_value' : 0 } }
        kdialog = KanoDialog ('Notice', 'This will send feedback to Kano now, are you sure?', dialog_buttons, parent_window=self)
        rc = kdialog.run()
        if rc == 0:
            # We are good to go, send network transaction
            self.send_feedback()

    def send_feedback(self, button=None, event=None):
        if not hasattr(event, 'keyval') or event.keyval == Gdk.KEY_Return:

            self.check_login()
            if not is_registered():
                return

            self.set_cursor_to_watch()
            self._submit_button.start_spinner()
            self._submit_button.set_sensitive(False)
            self.entry.set_sensitive(False)

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
                    self._submit_button.stop_spinner()
                    
                    title='Sent!'
                    description='Your feedback has been sumitted to Kano - Thank you!'
                    kdialog = KanoDialog(title, description, button_dict, parent_window=self)
                    kdialog.dialog.set_keep_above(False)
                    response = kdialog.run()

                    self._submit_button.set_sensitive(True)
                    self.entry.set_sensitive(True)

                    # Allow for interactive mouse events when transaction is complete
                    # and shrink the widget back to compact mode
                    self.in_submit=False
                    self.shrink_window()

                GObject.idle_add(done, title, description, button_dict)

            thread = threading.Thread(target=lengthy_process)
            thread.start()

    def set_cursor_to_watch(self):
        watch_cursor = Gdk.Cursor(Gdk.CursorType.WATCH)
        self.get_window().set_cursor(watch_cursor)
        self.scrolledwindow.get_window().set_cursor(watch_cursor)
        
    def set_cursor_to_normal(self):
        self.get_window().set_cursor(None)
        if self.in_submit:
            self.scrolledwindow.get_window().set_cursor(None)
        
    def send_user_info(self):
        # Text from Entry - the subject of the email
        subject = "Kano Desktop Feedback Widget"

        # Main body of the text
        textbuffer = self.entry.get_buffer()
        startiter, enditer = textbuffer.get_bounds()
        text = textbuffer.get_text(startiter, enditer, True)

        # Delegate the network transaction
        success, error = send_data(text, None, subject)
        return success, error

    def check_login(self):
        # Check if user is registered
        if not is_registered():
            # Show dialogue
            title = "Kano Login"
            description = "You need to login to Kano World before sending information. \nDo you want to continue?"
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
            kdialog.dialog.set_keep_above(False)
            self.set_keep_above(False)
            rc = kdialog.run()
            if rc == 0:
                Gtk.main_iteration()
                run_cmd('/usr/bin/kano-login')

            self.set_keep_above(True)
            del kdialog
            while Gtk.events_pending():
                Gtk.main_iteration()
