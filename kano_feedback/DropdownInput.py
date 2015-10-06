#!/usr/bin/env python

# DropdownInput.py
#
# Copyright (C) 2015 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#

from gi.repository import Gtk, GObject
from kano.gtk3.kano_combobox import KanoComboBox


class DropdownInput(Gtk.Alignment):
    __gsignals__ = {
        'dropdown-changed': (GObject.SIGNAL_RUN_FIRST, None, ()),
        "popup": (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self, values):
        super(DropdownInput, self).__init__()
        self._combo = KanoComboBox(items=values)
        KanoComboBox.apply_styling_to_screen()
        self._combo.connect("selected", self._emit_value_changed)

        # Propagate the dropdown widget popup signal
        self._combo.connect("popup", self._emit_popup)

        self.add(self._combo)

    def get_selected_text(self):
        return self._combo.get_selected_item_text()

    def _emit_value_changed(self, widget):
        self.emit('dropdown-changed')

    def _emit_popup(self, widget):
        self.emit('popup')

    def get_focusable_widget(self):
        '''
        :returns: tuple (bool, widget)
                  The first argument is whether there is a widget
                  that should be focused on, the second is the
                  widget in question
        '''
        return (True, self._combo)
