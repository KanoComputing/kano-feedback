#!/usr/bin/env python

# kano-feedback-widget.py
#
# Copyright (C) 2014 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
# Provides a simple UI interface to quickly send feedback to Kano
#

import os
import sys
from gi.repository import Gtk, Gdk

if __name__ == '__main__' and __package__ is None:
    dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if dir_path != '/usr':
        sys.path.insert(0, dir_path)

from kano_feedback.WidgetWindow import MainWindow

def position_widget(window):
    screen = Gdk.Screen.get_default()
    widget_x = (screen.get_width() - window.WIDTH) / 2
    widget_y = 10
    window.move(widget_x, widget_y)

def main():
    win = MainWindow()
    win.show_all()

    position_widget(win)
    
    Gtk.main()
    return 0

if __name__ == '__main__':
    sys.exit(main())
