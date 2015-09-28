#!/usr/bin/env python

# WidgetWindow.py
#
# Copyright (C) 2015 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#
# The MainWindow for the Desktop Feedback Widget
#

from gi.repository import Gtk, Gdk, GObject

from kano.gtk3.application_window import ApplicationWindow
from kano.gtk3.scrolled_window import ScrolledWindow
from kano.gtk3.buttons import OrangeButton
from kano.gtk3.apply_styles import apply_styling_to_screen, \
    apply_styling_to_widget
from DataSender import send_form
from kano_profile.tracker import track_action
from kano_feedback.WidgetQuestions import WidgetPrompts
from kano_feedback.Media import media_dir
from kano_feedback.SliderInput import SliderInput
from kano_feedback.RadioInput import RadioInput
from kano_feedback.CheckInput import CheckInput
from kano_feedback.DropdownInput import DropdownInput
from kano_feedback.TextInput import TextInput


class WidgetWindow(ApplicationWindow):
    CLOSE_FEEDBACK = 0
    KEEP_OPEN = 1
    LAUNCH_WIFI = 2
    WIDTH = 500
    HEIGHT_COMPACT = 50
    HEIGHT_EXPANDED = 200
    SUBJECT = 'Kano Desktop Feedback Widget'

    def __init__(self):
        ApplicationWindow.__init__(self, 'widget', self.WIDTH,
                                   self.HEIGHT_COMPACT)

        self.wprompts = WidgetPrompts()
        self.wprompts.load_prompts()

        self._initialise_window()

        if not self.wprompts.get_current_prompt():
            self.hide_until_more_questions()
            return

        self.position_widget()
        # Catch the window state event to avoid minimising and losing
        # the window
        self.connect("window-state-event", self._unminimise_if_minimised)

    def hide_until_more_questions(self):
        '''
        Hide the widget and set a timer to get new questions
        '''
        delay = 15 * 60 * 1000
        self.hide()
        GObject.timeout_add(delay, self.timer_fetch_questions)

        return

    def timer_fetch_questions(self):
        '''
        This function will periodically call the Questions API
        Until we get questions for the user, then show the widget again
        '''
        self.wprompts.load_prompts()
        nextp = self.wprompts.get_current_prompt()
        if nextp:
            self.set_keep_below(True)
            self.show()
            self.position_widget()
            self._shrink()

            self._prompt.set_text(nextp)

            # Only change the textbuffer if type is correct
            if self.wprompts.get_current_prompt_type() == "text":
                self._input_widget.get_buffer().set_text('')

            return False
        else:
            return True

    def position_widget(self):
        '''
        Position the widget window at the top center of the screen
        '''
        screen = Gdk.Screen.get_default()
        widget_x = (screen.get_width() - self.WIDTH) / 2
        widget_y = 20
        self.move(widget_x, widget_y)

    def _initialise_window(self):
        '''
        Inititlaises the gtk window
        '''
        self.last_click = 0

        self.app_name_opened = 'feedback-widget-opened'
        self.typeahead = None
        self.help_tip_message = 'Type your feedback here!'

        self.rotating_mode = True
        self.in_submit = False

        apply_styling_to_screen(media_dir() + 'css/widget.css')

        ScrolledWindow.apply_styling_to_screen(wide=False)

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

        self._prompt = prompt = Gtk.Label(self.wprompts.get_current_prompt(),
                                          hexpand=False)
        prompt.get_style_context().add_class('prompt')
        prompt.set_justify(Gtk.Justification.LEFT)
        prompt.set_alignment(0.1, 0.5)
        prompt.set_size_request(410, -1)
        prompt.set_line_wrap(True)

        prompt_container = Gtk.Table(1, 1, False)
        prompt_container.attach(prompt, 0, 1, 0, 1, Gtk.AttachOptions.SHRINK | Gtk.AttachOptions.FILL)

        grid.attach(prompt_container, 1, 0, 2, 1)

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

        # Create the scrolled window before deciding what to pack inside

        self._scrolledwindow = ScrolledWindow()
        self._scrolledwindow.set_hexpand(True)
        self._scrolledwindow.set_vexpand(True)
        self._scrolledwindow.set_margin_left(10)
        self._scrolledwindow.set_margin_right(10)
        self._scrolledwindow.set_margin_top(10)
        self._scrolledwindow.set_margin_bottom(10)
        self._scrolledwindow.set_policy(Gtk.PolicyType.AUTOMATIC,
                                        Gtk.PolicyType.AUTOMATIC)

        self._create_input_widget()

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

        self._dont_shrink = False
        self._shrink()

        self.connect("focus-out-event", self._shrink)
        self.connect("button-press-event", self._toggle)

    def _create_input_widget(self):
        # Unpack the contents of the scrolled window and replace with
        # another widget
        for child in self._scrolledwindow.get_children():
            self._scrolledwindow.remove(child)

            if self._input_widget:
                self._input_widget.destroy()

        # This needs to change depending on the type of the question.
        # If the type of the question is "text" or "textInput", then pack this,
        # otherwise pack other options.
        prompt_type = self.wprompts.get_current_prompt_type()

        if prompt_type:

            if prompt_type == "textInput":
                self._input_widget = self._create_text_input()

            elif prompt_type == "slider":
                start = self.wprompts.get_slider_start_value()
                end = self.wprompts.get_slider_end_value()
                self._input_widget = self._create_slider_input(start, end)

            elif prompt_type == "radio":
                radiobutton_labels = self.wprompts.get_current_choices()
                radiobutton_labels = map(str, radiobutton_labels)
                self._input_widget = self._create_radiobutton_input(radiobutton_labels)

            elif prompt_type == "checkbox":
                checkbox_labels = self.wprompts.get_current_choices()
                checkbox_labels = map(str, checkbox_labels)
                maximum = self.wprompts.get_checkbox_max_selected()
                minimum = self.wprompts.get_checkbox_min_selected()
                self._input_widget = self._create_checkbutton_input(
                    checkbox_labels, maximum, minimum
                )

            elif prompt_type == "dropdown":
                dropdown_labels = self.wprompts.get_current_choices()
                dropdown_labels = map(str, dropdown_labels)
                self._input_widget = self._create_dropdown_input(dropdown_labels)

            else:
                self._input_widget = self._create_text_input()
        else:
            self._input_widget = self._create_text_input()

        self._scrolledwindow.add(self._input_widget)

        # Force the widget to be realised
        self.show_all()

    def _set_anti_shrink_flag(self, widget, value):
        self._dont_shrink = value

    def _create_text_input(self):
        widget = TextInput()
        widget.connect("text-changed", self._set_send_sensitive)
        widget.connect("text-not-changed", self._set_send_insensitive)
        return widget

    def _create_slider_input(self, start, end):
        widget = SliderInput(start, end)
        widget.connect("slider-changed", self._set_send_sensitive)
        return widget

    def _create_radiobutton_input(self, values):
        widget = RadioInput(values)
        widget.connect("radio-changed", self._set_send_sensitive)
        return widget

    def _create_checkbutton_input(self, values, maximum, minimum):
        widget = CheckInput(values, maximum, minimum)
        widget.connect('min-not-selected', self._set_send_insensitive)
        widget.connect('min-selected', self._set_send_sensitive)
        return widget

    def _create_dropdown_input(self, values):
        widget = DropdownInput(values)
        widget.connect("dropdown-changed", self._set_send_sensitive)
        widget.connect("popup", self._set_anti_shrink_flag, True)
        widget.connect("dropdown-changed", self._set_anti_shrink_flag, False)
        return widget

    def _set_send_sensitive(self, widget=None):
        self._send.set_sensitive(True)

    def _set_send_insensitive(self, widget=None):
        self._send.set_sensitive(False)

    def _get_user_input(self):
        return self._input_widget.get_selected_text()

    def _shrink(self, widget=None, event=None):
        '''
        Hides the widget
        '''
        if not self._dont_shrink:
            self._x_button.hide()
            self._scrolledwindow.hide()
            self._gray_box.hide()
            self._send.hide()
            self._expanded = False

    def _expand(self, widget=None, event=None):
        '''
        Shows the text box
        '''
        self._x_button.show()
        self._scrolledwindow.show()
        self._gray_box.show()
        self._send.show()
        self._expanded = True

        (focusable, focus_widget) = self._input_widget.focusable_widget()
        if focusable:
            self.set_focus(focus_widget)

        # Add metrics to kano tracker
        track_action(self.app_name_opened)

    def _toggle(self, widget=None, event=None):
        '''
        Toggles between shrink-expand
        '''
        if self._expanded:
            self._shrink()
        else:
            self._expand()

    def _set_cursor_to_hand_cb(self, widget, data=None):
        widget.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.HAND1))

    def _send_clicked(self, window=None, event=None):
        self.blur()
        self.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.WATCH))

        while Gtk.events_pending():
            Gtk.main_iteration()

        prompt = self.wprompts.get_current_prompt()
        answer = self._get_user_input()

        # Don't send! Show an error?
        # Otherwise this shows as greyed out and with a spinner indefinitely
        if not answer:
            print "Not sending, no answer present"
            return

        qid = self.wprompts.get_current_prompt_id()

        if send_form(title=prompt, body=answer, question_id=qid):
            # Connection is ok, the answer has been sent
            self.wprompts.mark_prompt(prompt, answer, qid, offline=False, rotate=True)

            # Also send any pending answers we may have in the cache
            for offline in self.wprompts.get_offline_answers():
                sent_ok = send_form(title=offline[0], body=offline[1],
                                    question_id=offline[2], interactive=False)
                if sent_ok:
                    self.wprompts.mark_prompt(prompt=offline[0], answer=offline[1],
                                              qid=offline[2], offline=False, rotate=False)
        else:
            # Could not get connection, or user doesn't want to at this time
            # Save the answer as offline to send it later
            self.wprompts.mark_prompt(prompt, answer, qid, offline=True, rotate=True)

        # Get next available question on the queue
        nextp = self.wprompts.get_current_prompt()
        if nextp:
            self._create_input_widget()
            self._prompt.set_text(nextp)
            # This isn't needed anymore because the replace the text widget by default
            # self._input_widget.get_buffer().set_text('')

            # Disable send button
            self._send.set_sensitive(False)
            self._shrink()
        else:
            # There are no more questions available,
            # hide the widget until they arrive over the API
            self.hide_until_more_questions()

        self.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.ARROW))
        self.unblur()

    def _unminimise_if_minimised(self, window, event):
        # Check if we are attempting to minimise the window
        # if so, try to unminimise it
        if event.changed_mask & Gdk.WindowState.ICONIFIED:
            window.deiconify()
