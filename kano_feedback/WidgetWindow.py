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
        self.prompts=None
        self.current_prompt = None
        self.current_prompt_idx = 0
        self.last_click = 0

        self.app_name_opened = 'feedback-widget-opened'
        self.app_name_submitted = 'feedback-widget-submitted'

        self.typeahead = None
        self.help_tip_message = 'Type your feedback here!'

        self.rotating_mode=True
        self.in_submit=False
        self.load_prompts()
        self.rotating_prompt_window()

    def load_prompts(self):
        # Fetch prompts from a local file
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
        text = "What's your favorite part of Kano?"
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

        screen = Gdk.Screen.get_default()
        specific_provider = Gtk.CssProvider()
        specific_provider.load_from_path(Media.media_dir() + 'css/style.css')
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, specific_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        # The widget window has no frame or title bar or borders, and it always sits behind all top level windows
        self.visible=False
        self.set_hexpand(False)
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_keep_above(False)
        self.set_property('skip-taskbar-hint', True)

        self._grid = Gtk.Grid()
        self._grid.set_size_request(self.WIDTH, self.HEIGHT_COMPACT)
        self._grid.set_hexpand(False)

        # The rotating prompt goes here
        self.rotating_text = Gtk.Label(expand=False)
        self.rotating_text.set_hexpand(False)
        self.rotating_text.set_margin_left(10)
        self.rotating_text.set_margin_right(10)
        self.rotating_text.set_margin_top(10)
        self.rotating_text.set_margin_bottom(10)

        # Limit the maximum length the label can occupy horizontally
        self.rotating_text.set_max_width_chars(30)

        # Tell the label to wrap the text if it doesn't fit
        self.rotating_text.set_justify(Gtk.Justification.CENTER)
        self.rotating_text.set_line_wrap(True)
        self.rotating_text.set_line_wrap_mode(Gtk.WrapMode.WORD)
        self.rotating_text.set_size_request(self.WIDTH, -1)

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
            self.shrink_window(True)

    def shrink_button_clicked(self, window, event):
        self.shrink_window(True)

    def focus_out(self, window, event):
        self.shrink_window(True)

    def expand_window(self):
        self.rotating_mode=False

        # Add metrics to kano tracker
        add_runtime_to_app(self.app_name_opened, 0)

        # Add a shrink widget button
        self._shrink_button = Gtk.Button(label="X")
        self._shrink_button.connect("button_press_event", self.shrink_button_clicked)

        # The text input area: The message to send to Kano
        self._text = Gtk.TextView()
        self._text.set_margin_left(20)
        self._text.set_margin_right(20)
        self._text.set_margin_top(20)
        self._text.set_margin_bottom(20)

        self._text.set_editable(True)
        self._text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._text.set_size_request(self.WIDTH, -1)

        # Wrap the multiline text into a scrollable
        self.scrolledwindow = ScrolledWindow()
        self.scrolledwindow.set_vexpand(False)
        self.scrolledwindow.set_hexpand(False)
        self.scrolledwindow.add(self._text)
        self.scrolledwindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolledwindow.apply_styling_to_widget()
        self.scrolledwindow.set_margin_left(2)
        self.scrolledwindow.set_margin_right(2)
        self.scrolledwindow.set_margin_top(2)
        self.scrolledwindow.set_margin_bottom(2)
        self.scrolledwindow.set_size_request(self.WIDTH, self.HEIGHT_EXPANDED)

        # Prepare the edition area and provide either the previous typeahead or a short help message
        self._textbuffer = self._text.get_buffer()
        if self.typeahead:
            self._textbuffer.set_text(self.typeahead)
            self._text.get_style_context().add_class("active")
        else:
            self._textbuffer.set_text(self.help_tip_message)
            self._clear_buffer_handler_id = self._textbuffer.connect("insert-text", self.clear_buffer)

        self.scrolledwindow.add(self._text)
        self._grid.attach(self.scrolledwindow, 0, 1, 1, 1)

        # Create a Submit button
        self._send_button = KanoButton("Submit", "blue")
        self._send_button.connect("button_press_event", self.submit_clicked)
        if self.typeahead:
            self._send_button.set_sensitive(True)
        else:
            self._send_button.set_sensitive(False)

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

    def shrink_window(self, save_typeahead):
        if self.rotating_mode or self.in_submit:
            return
        else:
            self.rotating_mode=True

        # Save the feedback text currently typed in the widget
        if save_typeahead:
            textbuffer = self._text.get_buffer()
            startiter, enditer = textbuffer.get_bounds()
            self.typeahead = textbuffer.get_text(startiter, enditer, True)
        else:
            self.typeahead = None

        # Resize the window
        self._grid.set_size_request(self.WIDTH, self.HEIGHT_COMPACT)

        # Remove unnecessary widgets from the grid and display current prompt
        self._grid.remove(self.scrolledwindow)
        self._grid.remove(self.submit_box)
        self._grid.remove(self._shrink_button)
        self.rotating_text.set_text (self.get_current_prompt())
        self._grid.show_all()

    def after_feedback_sent(self, completed):
        self.in_submit=False
        if completed:
            self.current_prompt=self.get_next_prompt()
            self.shrink_window(False)

        # Add metrics to kano tracker
        add_runtime_to_app(self.app_name_submitted, 0)

    def submit_clicked(self, window, event):
        self.in_submit=True        
        self.send_feedback(body_title=self.get_current_prompt())
