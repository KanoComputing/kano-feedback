#!/usr/bin/env python

# CheckInput.py
#
# Copyright (C) 2015 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#

from gi.repository import Gtk, GObject


class CheckInput(Gtk.Box):
    __gsignals__ = {
        'check-changed': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'min-selected': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'min-not-selected': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self, values, maximum, minimum):
        super(CheckInput, self).__init__()
        self._maximum = maximum
        self._minimum = minimum
        self._buttons = []

        for v in values:
            _check = Gtk.CheckButton.new_with_label(v)
            # The callback checks how many of the buttons have been selected,
            # and if it's the maximum, then the remaining should be disabled
            self.pack_start(_check, False, False, 10)
            self._buttons.append(_check)
            # Connect to event listener

        for b in self._buttons:
            b.connect("toggled", self._checkbutton_cb)

    def get_selected_text(self):
        selected_text = []
        for button in self._buttons:
            if button.get_active():
                selected_text.append(button.get_label())

        return str(selected_text)

    def _checkbutton_cb(self, widget):
        self.emit('check-changed')
        self._set_sensitive_buttons()

    def _set_sensitive_buttons(self):
        selected = 0

        for button in self._buttons:
            if button.get_active():
                selected += 1

        if selected >= self._maximum:
            for button in self._buttons:
                if not button.get_active():
                    button.set_sensitive(False)
        else:
            # Tell anything hooked into this widget that the min
            # number of buttons have been selected
            if selected >= self._minimum:
                self.emit("min-selected")
            else:
                self.emit("min-not-selected")

            for button in self._buttons:
                if not button.get_active():
                    button.set_sensitive(True)

    def focusable_widget(self):
        return (False, None)
