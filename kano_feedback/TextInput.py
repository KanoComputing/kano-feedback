#!/usr/bin/env python

# TextInput.py
#
# Copyright (C) 2015 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU GPL v2
#

from gi.repository import Gtk, GObject


class TextInput(Gtk.Alignment):
    __gsignals__ = {
        'text-changed': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'text-not-changed': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self):
        super(TextInput, self).__init__()
        self._textview = Gtk.TextView()
        self._textview.get_style_context().add_class('active')
        self._textview.set_hexpand(False)
        self._textview.set_vexpand(False)
        self._textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._textview.get_buffer().connect('changed', self._text_changed)

        self.add(self._textview)

    def focusable_widget(self):
        return (True, self._textview)

    def _get_text_from_textbuffer(self, text_buffer):
        startiter, enditer = text_buffer.get_bounds()
        return text_buffer.get_text(startiter, enditer, True)

    def _text_changed(self, text_buffer):
        buff_text = self._get_text_from_textbuffer(text_buffer)

        # Only allow answers containing non-space text
        enable_send = len(buff_text.strip('\t\n ')) > 0

        if enable_send:
            self.emit('text-changed')
        else:
            self.emit('text-not-changed')

    def _emit_value_changed(self, widget):
        self.emit('text-changed')

    def get_selected_text(self):
        textbuffer = self._textview.get_buffer()
        return self._get_text_from_textbuffer(textbuffer)
