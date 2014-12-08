#!/usr/bin/env python

# WidgetWindow.py
#
# Copyright (C) 2014 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
# The MainWindow for the Desktop Feedback Widget
#

from kano_feedback.MainWindow import *
import json
import requests

from kano_profile.tracker import add_runtime_to_app

class WidgetWindow(MainWindow):
    CLOSE_FEEDBACK = 0
    KEEP_OPEN = 1
    LAUNCH_WIFI = 2
    WIDTH = 400
    HEIGHT_COMPACT = 50
    HEIGHT_EXPANDED = 200
    SUBJECT = 'Kano Desktop Feedback Widget'

    def __init__(self):
        MainWindow.__init__(self, subject=self.SUBJECT)

        self.prompts_file='/usr/share/kano-feedback/media/widget/prompts.json'
        self.prompts_url='http://dev.kano.me/temp/widget-prompts.json'
        self.prompts=None
        self.current_prompt = None
        self.current_prompt_idx = 0
        self.last_click = 0

        self.app_name_opened = 'feedback-widget-opened'
        self.app_name_submitted = 'feedback-widget-submitted'

        self.rotating_mode=True
        self.in_submit=False
        self.load_prompts()
        self.rotating_prompt_window()

    def load_prompts(self):
        # Periodically fetch a list of prompts from the network, or a local file if not available
        if is_internet():
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

    def get_current_prompt(self):
        if not self.current_prompt:
            self.current_prompt=self.get_next_prompt()

        return self.current_prompt

    def get_next_prompt(self):
        text = 'Click here to send feedback to Kano'
        try:
            text = self.prompts[self.current_prompt_idx]['text']
            if self.current_prompt_idx == len(self.prompts) - 1:
                self.current_prompt_idx = 0
            else:
                self.current_prompt_idx += 1
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
        
        # FIXME: none of these methods are centering the label text
        #self.rotating_text.set_halign(Gtk.Align.CENTER)
        #self.rotating_text.set_justify(Gtk.Justification.CENTER)
        #self.rotating_text.set_alignment(0.5, 0.5)

        self.rotating_text.set_text (self.get_current_prompt())

        # When the widget is clicked, it will be expanded or compacted
        self.connect("button_press_event", self.window_clicked)

        self._grid.attach(self.rotating_text, 0, 0, 1, 1)

        # And when the widget loses interactive focus it will shrink back again
        self.connect("focus-out-event", self.focus_out)

        self._grid.set_row_spacing(0)
        self.set_main_widget(self._grid)

    def window_clicked(self, window, event):
        # Protect against fast repeated mouse clicks (time expressed in ms)
        min_time_between_clicks=1000
        if not self.last_click:
            self.last_click=event.get_time()
        else:
            if (event.get_time() - self.last_click) < min_time_between_clicks or self.in_submit:
                self.last_click=event.get_time()
                return
            else:
                self.last_click=event.get_time()

        if self.rotating_mode:
            self.expand_window()
        else:
            self.shrink_window()

    def shrink_button_clicked(self, window, event):
        self.shrink_window()

    def focus_out(self, window, event):
        self.shrink_window()

    def expand_window(self):
        self.rotating_mode=False

        # Add metrics to kano tracker
        add_runtime_to_app(self.app_name_opened, 0)

        # Add a shrink widget button
        self._shrink_button = Gtk.Button(label="X")
        self._shrink_button.connect("button_press_event", self.shrink_button_clicked)

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
        self._text = Gtk.TextView()
        self._text.set_margin_left(20)
        self._text.set_margin_right(20)
        self._text.set_margin_top(20)
        self._text.set_margin_bottom(20)

        self._text.set_editable(True)
        self._text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._text.set_size_request(self.WIDTH, -1)

        self._textbuffer = self._text.get_buffer()
        self._textbuffer.set_text("Type your feedback here man!")
        self._clear_buffer_handler_id = self._textbuffer.connect("insert-text", self.clear_buffer)

        self.scrolledwindow.add(self._text)
        self._grid.attach(self.scrolledwindow, 0, 1, 1, 1)

        # Create a Submit button
        # TODO: If there is no internet do not enable the button, display a message instead
        self._send_button = KanoButton("Submit", "blue")
        self._send_button.connect("button_press_event", self.submit_clicked)
        
        # Create a box that will hold the button
        self.submit_box = Gtk.ButtonBox()
        self.submit_box.set_layout(Gtk.ButtonBoxStyle.CENTER)
        self.submit_box.set_spacing(20)

        # Put the submit button inside the box
        self.submit_box.pack_start(self._send_button, False, False, 0)
        self.submit_box.set_child_non_homogeneous(self._send_button, True)
        self.submit_box.set_margin_bottom(20)

        # Add the button box inside the grid
        self._grid.attach(self.submit_box, 0, 2, 1, 1)
        self._grid.attach_next_to(self._shrink_button, self.rotating_text, Gtk.PositionType.RIGHT, 2, 1)

        self._grid.show_all()

    def shrink_window(self):
        if self.rotating_mode or self.in_submit:
            return
        else:
            self.rotating_mode=True

        # Resize the window
        self._grid.set_size_request(self.WIDTH, self.HEIGHT_COMPACT)

        # Remove unnecessary widgets from the grid and display current prompt
        self._grid.remove(self.scrolledwindow)
        self._grid.remove(self.submit_box)
        self._grid.remove(self._shrink_button)
        self.rotating_text.set_text (self.get_current_prompt())
        self._grid.show_all()

    def after_feedback_sent(self):
        self.shrink_window()
        self.in_submit=False
        
        # Add metrics to kano tracker
        add_runtime_to_app(self.app_name_submitted, 0)

        self.current_prompt=self.get_next_prompt()

    def submit_clicked(self, window, event):
        self.in_submit=True
        self.send_feedback()