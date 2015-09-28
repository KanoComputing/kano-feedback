#!/usr/bin/env python

# RadioInput.py
#
# Copyright (C) 2015 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#

from gi.repository import Gtk, GObject


class RadioInput(Gtk.Box):
    __gsignals__ = {
        'radio-changed': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self, values):
        super(RadioInput, self).__init__()
        buttons = []

        # First value is treated differently
        first_value = values[0]
        self._first_radio = Gtk.RadioButton.new_with_label(None, first_value)
        self._first_radio.connect(
            'toggled',
            self._emit_value_changed,
            first_value
        )
        self.pack_start(self._first_radio, False, False, 20)
        values.pop(0)

        for v in values:
            radio = Gtk.RadioButton.new_with_label_from_widget(
                self._first_radio, v
            )
            self.pack_start(radio, False, False, 10)
            buttons.append(radio)

    def _emit_value_changed(self, widget, value):
        self.emit('radio-changed')

    def get_selected_text(self):
        group = self._first_radio.get_group()
        for button in group:
            if button.get_active():
                return str(button.get_label())

        print "no selected text for radiobuttons"

    def focusable_widget(self):
        return (False, None)
