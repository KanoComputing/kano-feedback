#!/usr/bin/env python

# WidgetWindow.py
#
# Copyright (C) 2014 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
# The MainWindow for the Desktop Feedback Widget
#

import json
from gi.repository import Gtk, Gdk

from kano_feedback.Media import media_dir
from kano.gtk3.application_window import ApplicationWindow
from kano.gtk3.scrolled_window import ScrolledWindow
from kano.gtk3.buttons import OrangeButton
from kano.gtk3.apply_styles import apply_styling_to_screen, \
    apply_styling_to_widget
from DataSender import send_feedback

from kano_profile.tracker import add_runtime_to_app


class WidgetWindow(ApplicationWindow):
    CLOSE_FEEDBACK = 0
    KEEP_OPEN = 1
    LAUNCH_WIFI = 2
    WIDTH = 500
    HEIGHT_COMPACT = 50
    HEIGHT_EXPANDED = 200
    SUBJECT = 'Kano Desktop Feedback Widget'

    def __init__(self):
        ApplicationWindow.__init__(self, 'Report a Problem', self.WIDTH,
                                   self.HEIGHT_COMPACT)

        self.prompts_file = '/usr/share/kano-feedback/media/widget/prompts.json'
        self.prompts = None
        self.current_prompt = None
        self.current_prompt_idx = 0
        self.last_click = 0

        self.app_name_opened = 'feedback-widget-opened'
        self.app_name_submitted = 'feedback-widget-submitted'

        self.typeahead = None
        self.help_tip_message = 'Type your feedback here!'

        self.rotating_mode = True
        self.in_submit = False
        self.load_prompts()

        apply_styling_to_screen(media_dir() + 'css/widget.css')

        ScrolledWindow.apply_styling_to_screen(wide=False)

        self._initialise_window()

    def _initialise_window(self):
        self.visible = False
        self.set_hexpand(False)
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_keep_above(False)
        self.set_property('skip-taskbar-hint', True)

        self._grid = grid = Gtk.Grid(hexpand=True, vexpand=True)

        qmark = Gtk.Label('?')
        qmark.get_style_context().add_class('qmark')

        qmark_centering = Gtk.Alignment(xalign=0.5, yalign=0.5)
        qmark_centering.add(qmark)

        qmark_box = Gtk.EventBox()
        qmark_box.get_style_context().add_class('qmark_box')
        qmark_box.add(qmark_centering)
        qmark_box.set_size_request(self.HEIGHT_COMPACT, self.HEIGHT_COMPACT)

        grid.attach(qmark_box, 0, 0, 1, 1)

        self._prompt = prompt = Gtk.Label(self.get_current_prompt(),
                                          hexpand=True)
        prompt.get_style_context().add_class('prompt')
        prompt.set_justify(Gtk.Justification.FILL)
        prompt.set_max_width_chars(40)

        grid.attach(prompt, 1, 0, 2, 1)

        self._x_button = x_button = Gtk.Button('x')
        x_button.set_size_request(20, 20)
        x_button.connect('clicked', self._shrink)
        x_button.get_style_context().add_class('x_button')
        x_button.set_margin_right(20)

        x_button_ebox = Gtk.EventBox()
        x_button_ebox.add(x_button)
        x_button_ebox.connect("realize", self._set_cursor_to_hand_cb)

        x_button_align = Gtk.Alignment(xalign=1, yalign=0.5,
                                       xscale=0, yscale=0)
        x_button_align.add(x_button_ebox)

        grid.attach(x_button_align, 2, 0, 1, 1)

        self._gray_box = gray_box = Gtk.EventBox()
        gray_box.get_style_context().add_class('gray_box')
        gray_box.set_size_request(-1,
                                  self.HEIGHT_EXPANDED - self.HEIGHT_COMPACT)

        gray_box_centering = Gtk.Alignment(xalign=0, yalign=0, xscale=1.0,
                                           yscale=1.0)
        gray_box_centering.add(gray_box)

        grid.attach(gray_box_centering, 0, 1, 1, 2)

        self._text = Gtk.TextView()
        self._text.get_style_context().add_class('active')
        self._text.set_hexpand(False)
        self._text.set_vexpand(False)
        self._text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)

        self._text.get_buffer().connect('changed', self._text_changed)

        text_align = Gtk.Alignment(xalign=0, yalign=0, xscale=1, yscale=1)
        text_align.add(self._text)

        self._scrolledwindow = ScrolledWindow()
        self._scrolledwindow.add(text_align)
        self._scrolledwindow.set_hexpand(True)
        self._scrolledwindow.set_vexpand(True)
        self._scrolledwindow.set_margin_left(10)
        self._scrolledwindow.set_margin_right(10)
        self._scrolledwindow.set_margin_top(10)
        self._scrolledwindow.set_margin_bottom(10)
        self._scrolledwindow.set_policy(Gtk.PolicyType.AUTOMATIC,
                                        Gtk.PolicyType.AUTOMATIC)

        sw_ebox = Gtk.EventBox()
        sw_ebox.get_style_context().add_class('scrolled_win')
        sw_ebox.add(self._scrolledwindow)

        grid.attach(sw_ebox, 1, 1, 2, 1)

        self._send = send = OrangeButton('SEND')
        apply_styling_to_widget(send.label, media_dir() + 'css/widget.css')
        send.set_sensitive(False)
        send.connect('clicked', self._send_clicked)
        send.set_margin_left(10)
        send.set_margin_right(20)
        send.set_margin_top(10)
        send.set_margin_bottom(15)
        send_align = Gtk.Alignment(xalign=1, yalign=0.5, xscale=0, yscale=0)
        send_align.add(send)

        grid.attach(send_align, 2, 2, 1, 1)

        self.set_main_widget(grid)
        self.show_all()

        self._shrink()

        self.connect("focus-out-event", self._shrink)
        self.connect("button-press-event", self._toggle)

    def _shrink(self, widget=None, event=None):
        self._x_button.hide()
        self._scrolledwindow.hide()
        self._gray_box.hide()
        self._send.hide()
        self._expanded = False

    def _expand(self, widget=None, event=None):
        self._x_button.show()
        self._scrolledwindow.show()
        self._gray_box.show()
        self._send.show()
        self._expanded = True
        self.set_focus(self._text)

        # Add metrics to kano tracker
        add_runtime_to_app(self.app_name_opened, 0)

    def _toggle(self, widget=None, event=None):
        if self._expanded:
            self._shrink()
        else:
            self._expand()

    def _textview_focus_in(self, widget, event):
        self._text.get_style_context().add_class('active')

    def _textview_focus_out(self, widget, event):
        self._text.get_style_context().remove_class('active')

    def _set_cursor_to_hand_cb(self, widget, data=None):
        widget.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.HAND1))

    def _send_clicked(self, window=None, event=None):
        self.blur()
        self.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.WATCH))

        while Gtk.events_pending():
            Gtk.main_iteration()

        text = self._get_text_from_textbuffer(self._text.get_buffer())
        if send_feedback(self.get_current_prompt(), text):
            self._set_next_prompt()
            self._text.get_buffer().set_text('')
            self._shrink()

        self.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.ARROW))
        self.unblur()

    def _set_next_prompt(self):
        self.current_prompt = self.get_next_prompt()
        self._prompt.set_text(self.get_current_prompt())

    def _text_changed(self, text_buffer):
        buff_text = self._get_text_from_textbuffer(text_buffer)
        self._send.set_sensitive(len(buff_text) > 0)

    def _get_text_from_textbuffer(self, text_buffer):
        startiter, enditer = text_buffer.get_bounds()

        return text_buffer.get_text(startiter, enditer, True)

    def load_prompts(self):
        # Fetch prompts from a local file
        if not self.prompts:
            try:
                with open(self.prompts_file, 'r') as f:
                    prompts = json.loads(f.read())
                self.prompts = sorted(prompts, key=lambda k: k['priority'])
            except:
                pass

    def get_current_prompt(self):
        if not self.current_prompt:
            self.current_prompt = self.get_next_prompt()

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
