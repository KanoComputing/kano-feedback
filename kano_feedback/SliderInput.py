#!/usr/bin/env python

# SliderInput.py
#
# Copyright (C) 2015 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#

from gi.repository import Gtk, GObject


class SliderInput(Gtk.Box):
    __gsignals__ = {
        'slider-changed': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self, start, end):
        super(SliderInput, self).__init__(orientation=Gtk.Orientation.VERTICAL)

        self._start = start
        self._end = end

        # Make the selected value the halfway point
        value = int((start + end) / 2)

        self._scale = Gtk.HScale(
            adjustment=Gtk.Adjustment(
                value=value,
                lower=start,
                upper=end,
                step_increment=1,
                page_incr=0,
                page_size=0
            )
        )
        self._scale.set_digits(0)
        self._scale.connect('value-changed', self._emit_value_changed)

        slider_align = Gtk.Alignment(xalign=0, yalign=0, xscale=1, yscale=1)
        slider_align.add(self._scale)

        self.pack_start(slider_align, False, False, 0)

    def _emit_value_changed(self, widget):
        self.emit('slider-changed')

    def get_selected_text(self):
        return str(self._scale.get_value())

    def get_focusable_widget(self):
        '''
        :returns: tuple (bool, widget)
                  The first argument is whether there is a widget
                  that should be focused on, the second is the
                  widget in question
        '''
        return (True, self._scale)
