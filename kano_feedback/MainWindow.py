#!/usr/bin/env python

# MainWindow.py
#
# Copyright (C) 2014 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#
# The MainWindow class
#

import sys
from gi.repository import Gtk, Gdk, GObject, GdkPixbuf
import threading

GObject.threads_init()

from kano.gtk3.top_bar import TopBar
from DataSender import (send_data, take_screenshot, copy_screenshot, delete_tmp_dir,
                        create_tmp_dir, SCREENSHOT_NAME, SCREENSHOT_PATH, delete_screenshot)
from kano.utils import run_cmd
from kano_world.functions import is_registered
from kano.network import is_internet
from kano.gtk3.cursor import attach_cursor_events
from kano.gtk3.kano_dialog import KanoDialog
from kano.gtk3.buttons import KanoButton
from kano.gtk3.scrolled_window import ScrolledWindow
from kano.gtk3.application_window import ApplicationWindow
from kano_feedback import Media


class MainWindow(ApplicationWindow):
    CLOSE_FEEDBACK = 0
    KEEP_OPEN = 1
    LAUNCH_WIFI = 2
    WIDTH = 400

    def __init__(self, bug_report=False):
        self.bug_report = bug_report
        if self.bug_report:
            self.report_window()
        else:
            self.contact_window()

    def contact_window(self):

        # delete the directory containing all the info we'll send, and recreate
        delete_tmp_dir()
        create_tmp_dir()

        ApplicationWindow.__init__(self, 'Contact Us', self.WIDTH, 0.35)

        screen = Gdk.Screen.get_default()
        specific_provider = Gtk.CssProvider()
        specific_provider.load_from_path(Media.media_dir() + 'css/style.css')
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, specific_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        self.set_icon_name("feedback")
        # Make sure this window is always above
        self.set_keep_above(True)

        self._grid = Gtk.Grid()

        # Create top bar
        self._top_bar = TopBar(title="Contact Us", window_width=self.WIDTH, has_buttons=False)
        self._top_bar.set_close_callback(Gtk.main_quit)
        self.set_decorated(True)
        self.set_titlebar(self._top_bar)

        # Create Text view
        self._text = Gtk.TextView()
        self._text.set_editable(True)
        self._text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._text.set_size_request(self.WIDTH, -1)

        self._textbuffer = self._text.get_buffer()
        self._textbuffer.set_text("Type your feedback here!")
        self._clear_buffer_handler_id = self._textbuffer.connect("insert-text", self.clear_buffer)

        scrolledwindow = ScrolledWindow()
        scrolledwindow.set_vexpand(True)
        scrolledwindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolledwindow.apply_styling_to_widget()
        scrolledwindow.add(self._text)
        scrolledwindow.set_margin_left(2)
        scrolledwindow.set_margin_right(2)
        scrolledwindow.set_margin_top(2)
        scrolledwindow.set_margin_bottom(2)

        # Very hacky way to get a border: create a grey event box which is a little bigger than the widget below
        border = Gtk.EventBox()
        border.get_style_context().add_class("grey")
        border.add(scrolledwindow)
        self._grid.attach(border, 0, 0, 1, 1)
        border.set_margin_left(20)
        border.set_margin_right(20)
        border.set_margin_top(10)
        border.set_margin_bottom(20)

        # Create send button
        self._send_button = KanoButton("SEND")
        self._send_button.set_sensitive(False)
        self._send_button.connect("button_press_event", self.send_feedback)
        self._send_button.pack_and_align()
        self._send_button.align.set_padding(10, 10, 0, 0)

        bottom_background = Gtk.EventBox()
        bottom_background.get_style_context().add_class("grey")
        bottom_background.add(self._send_button.align)

        self._grid.attach(bottom_background, 0, 1, 1, 1)

        self._grid.set_row_spacing(0)
        self.set_main_widget(self._grid)

        # kano-profile stat collection
        try:
            from kano_profile.badges import increment_app_state_variable_with_dialog
            increment_app_state_variable_with_dialog('kano-feedback', 'starts', 1)
        except Exception:
            pass

    def report_window(self):
        ApplicationWindow.__init__(self, 'Report a Problem', self.WIDTH, 0.35)

        screen = Gdk.Screen.get_default()
        specific_provider = Gtk.CssProvider()
        specific_provider.load_from_path(Media.media_dir() + 'css/style.css')
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, specific_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        self.set_icon_name("feedback")
        # Make sure this window is always above
        self.set_keep_above(True)

        self._grid = Gtk.Grid()

        # Create top bar
        self._top_bar = TopBar(title="Report a Problem", window_width=self.WIDTH, has_buttons=False)
        self._top_bar.set_close_callback(Gtk.main_quit)
        self.set_decorated(True)
        self.set_titlebar(self._top_bar)

        self.entry = Gtk.Entry()
        self.entry.props.placeholder_text = "Add subject (optional)"
        self.entry.set_margin_left(20)
        self.entry.set_margin_right(20)
        self.entry.set_margin_top(20)
        self.entry.set_margin_bottom(10)
        self._grid.attach(self.entry, 0, 0, 1, 1)

        # Create Text view
        self._text = Gtk.TextView()
        self._text.set_editable(True)
        self._text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._text.set_size_request(self.WIDTH, -1)

        self._textbuffer = self._text.get_buffer()
        self._textbuffer.set_text("Type your problem here!")

        self._clear_buffer_handler_id = self._textbuffer.connect("insert-text", self.clear_buffer)

        scrolledwindow = ScrolledWindow()
        scrolledwindow.set_vexpand(True)
        scrolledwindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolledwindow.apply_styling_to_widget()
        scrolledwindow.add(self._text)
        scrolledwindow.set_margin_left(2)
        scrolledwindow.set_margin_right(2)
        scrolledwindow.set_margin_top(2)
        scrolledwindow.set_margin_bottom(2)

        # Very hacky way to get a border: create a grey event box which is a little bigger than the widget below
        border = Gtk.EventBox()
        border.get_style_context().add_class("grey")
        border.add(scrolledwindow)
        self._grid.attach(border, 0, 1, 1, 1)
        border.set_margin_left(20)
        border.set_margin_right(20)
        border.set_margin_top(10)
        border.set_margin_bottom(20)

        # Create take screenshot button
        self._screenshot_button = KanoButton("TAKE SCREENSHOT", "blue")
        self._screenshot_button.set_sensitive(True)
        self._screenshot_button.connect("button_press_event", self.screenshot_clicked)

        # Create attach screenshot button
        self._attach_button = KanoButton("ADD IMAGE", "blue")
        self._attach_button.set_sensitive(True)
        self._attach_button.connect("button_press_event", self.attach_clicked)

        # Create send button
        self._send_button = KanoButton("SEND")
        self._send_button.set_sensitive(False)
        self._send_button.connect("button_press_event", self.send_feedback)
        self._send_button.pack_and_align()
        self._send_button.set_margin(10, 0, 10, 0)

        self.screenshot_box = Gtk.ButtonBox()
        self.screenshot_box.set_layout(Gtk.ButtonBoxStyle.CENTER)
        self.screenshot_box.set_spacing(20)
        self.pack_screenshot_buttons()
        self.screenshot_box.set_margin_bottom(20)

        self._grid.attach(self.screenshot_box, 0, 2, 1, 1)

        # Create grey box to put the button in
        self.bottom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.bottom_box.pack_start(self._send_button.align, False, False, 0)

        bottom_background = Gtk.EventBox()
        bottom_background.get_style_context().add_class("grey")
        bottom_background.add(self.bottom_box)

        self._grid.attach(bottom_background, 0, 3, 1, 1)

        self._grid.set_row_spacing(0)
        self.set_main_widget(self._grid)

        # kano-profile stat collection
        try:
            from kano_profile.badges import increment_app_state_variable_with_dialog
            increment_app_state_variable_with_dialog('kano-feedback', 'starts', 1)
        except Exception:
            pass

    def send_feedback(self, button=None, event=None):
        if not hasattr(event, 'keyval') or event.keyval == Gdk.KEY_Return:

            self.check_login()
            if not is_registered():
                return

            if self.bug_report:
                title = "Important"
                description = "Your feedback will include debugging information. \nDo you want to continue?"
                kdialog = KanoDialog(
                    title, description,
                    {
                        "CANCEL":
                        {
                            "return_value": 1
                        },
                        "OK":
                        {
                            "return_value": 0
                        }
                    },
                    parent_window=self
                )
                rc = kdialog.run()
                if rc != 0:
                    # Enable button and refresh
                    button.set_sensitive(True)
                    Gtk.main_iteration()
                    return

            self.set_cursor_to_watch()
            self._send_button.start_spinner()
            self._send_button.set_sensitive(False)
            self._text.set_sensitive(False)

            def lengthy_process():
                button_dict = {"OK": {"return_value": self.CLOSE_FEEDBACK}}

                if not is_internet():
                    title = "No internet connection"
                    description = "Configure your connection"

                    button_dict = {"OK": {"return_value": self.LAUNCH_WIFI}}
                else:
                    success, error = self.send_user_info()

                    if success:
                        title = "Info"
                        description = "Feedback sent correctly"
                        button_dict = \
                            {
                                "OK":
                                {
                                    "return_value": self.CLOSE_FEEDBACK
                                }
                            }
                    else:
                        title = "Info"
                        description = "Something went wrong, error: {}".format(error)
                        button_dict = \
                            {
                                "CLOSE FEEDBACK":
                                {
                                    "return_value": self.CLOSE_FEEDBACK,
                                    "color": "red"
                                },
                                "TRY AGAIN":
                                {
                                    "return_value": self.KEEP_OPEN,
                                    "color": "green"
                                }
                            }

                def done(title, description, button_dict):

                    self.set_cursor_to_normal()
                    self._send_button.stop_spinner()
                    self._send_button.set_sensitive(True)
                    self._text.set_sensitive(True)

                    # If the user decides to launch the wifi config,
                    # the window needs to be able to go below kano-settings
                    self.set_keep_above(False)

                    kdialog = KanoDialog(title, description, button_dict, parent_window=self)
                    kdialog.dialog.set_keep_above(False)
                    response = kdialog.run()

                    if response == self.LAUNCH_WIFI:
                        run_cmd('sudo /usr/bin/kano-settings 4')
                    elif response == self.CLOSE_FEEDBACK:
                        sys.exit(0)

                GObject.idle_add(done, title, description, button_dict)

            thread = threading.Thread(target=lengthy_process)
            thread.start()

    def set_cursor_to_watch(self):
        watch_cursor = Gdk.Cursor(Gdk.CursorType.WATCH)
        self.get_window().set_cursor(watch_cursor)
        self._text.get_window(Gtk.TextWindowType.TEXT).set_cursor(watch_cursor)
        self._text.get_window(Gtk.TextWindowType.WIDGET).set_cursor(watch_cursor)

    def set_cursor_to_normal(self):
        self.get_window().set_cursor(None)
        self._text.get_window(Gtk.TextWindowType.TEXT).set_cursor(None)
        self._text.get_window(Gtk.TextWindowType.WIDGET).set_cursor(None)

    def send_user_info(self):
        # Text from Entry - the subject of the email
        if hasattr(self, "entry"):
            subject = self.entry.get_text()
        else:
            subject = "Kano feedback submission"

        # Main body of the text
        textbuffer = self._text.get_buffer()
        startiter, enditer = textbuffer.get_bounds()
        text = textbuffer.get_text(startiter, enditer, True)

        success, error = send_data(text, self.bug_report, subject)

        return success, error

    def open_help(self, button=None, event=None):
        run_cmd("/usr/bin/kano-help-launcher")

    def clear_buffer(self, textbuffer, textiter, text, length):
        self._text.get_style_context().add_class("active")

        start = textbuffer.get_start_iter()
        textbuffer.delete(start, textiter)
        textbuffer.disconnect(self._clear_buffer_handler_id)

        self._send_button.set_sensitive(True)

    def screenshot_clicked(self, button=None, event=None):
        self.iconify()
        take_screenshot()
        self.include_screenshot()
        self.deiconify()

    def attach_clicked(self, button=None, event=None):
        screenshot = None
        # Open file manager
        dialog = Gtk.FileChooserDialog("Please choose a file", self, Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        self.add_filters(dialog)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            screenshot = dialog.get_filename()

        dialog.destroy()
        # Copy image file into feedback folder
        if screenshot is not None:
            copy_screenshot(screenshot)
            self.include_screenshot()

    def add_filters(self, dialog):
        # Image filter
        filter_images = Gtk.FileFilter()
        filter_images.set_name("Images")
        filter_images.add_mime_type("image/png")
        filter_images.add_mime_type("image/jpeg")
        filter_images.add_mime_type("image/gif")
        filter_images.add_pattern("*.png")
        filter_images.add_pattern("*.jpg")
        filter_images.add_pattern("*.gif")
        filter_images.add_pattern("*.tif")
        filter_images.add_pattern("*.xpm")
        dialog.add_filter(filter_images)

        # Any file filter
        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

    def iconify(self):
        self.hide()

    def deiconify(self):
        self.show_all()

    # this is the box containing the filename of the screenshot,
    # and the option to display it or remove it
    def include_screenshot(self):
        if not hasattr(self, "screenshot"):
            self.screenshot = Gtk.EventBox()
            self.screenshot.get_style_context().add_class("kano_button")
            self.screenshot.get_style_context().add_class("blue_background")

            remove_screenshot = Gtk.Button()
            attach_cursor_events(remove_screenshot)
            remove_icon = Gtk.Image.new_from_file("/usr/share/kano-feedback/media/icons/close.png")
            remove_screenshot.add(remove_icon)
            remove_screenshot.connect("button-release-event", self.remove_screenshot)
            remove_screenshot.get_style_context().add_class("blue_background")

            show_screenshot = Gtk.Button()
            attach_cursor_events(show_screenshot)
            show_icon = Gtk.Image()
            show_icon.set_from_file("/usr/share/kano-feedback/media/icons/preview.png")
            show_screenshot.add(show_icon)
            show_screenshot.connect("button-release-event", self.show_screenshot)
            show_screenshot.get_style_context().add_class("blue_background")

            label = Gtk.Label(SCREENSHOT_NAME.upper())
            label.set_padding(10, 0)
            box = Gtk.Box()
            box.pack_start(label, False, False, 0)
            box.pack_end(remove_screenshot, False, False, 0)
            box.pack_end(show_screenshot, False, False, 0)

            self.screenshot.add(box)

        self.screenshot_box.remove(self._screenshot_button)
        self.screenshot_box.remove(self._attach_button)
        self.screenshot_box.pack_start(self.screenshot, False, False, 0)

    def remove_screenshot(self, widget, event):
        delete_screenshot()
        self.screenshot_box.remove(self.screenshot)
        self.pack_screenshot_buttons()
        self.show_all()

    def show_screenshot(self, widget, event):
        height = Gdk.Screen().get_default().get_height()
        width = Gdk.Screen().get_default().get_width()
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(SCREENSHOT_PATH, width * 0.5, height * 0.5)
        image = Gtk.Image.new_from_pixbuf(pixbuf)

        dialog = KanoDialog("Screenshot", widget=image)
        dialog.run()

    def pack_screenshot_buttons(self):
        self.screenshot_box.pack_start(self._screenshot_button, False, False, 0)
        self.screenshot_box.set_child_non_homogeneous(self._screenshot_button, True)
        self.screenshot_box.pack_start(self._attach_button, False, False, 0)
        self.screenshot_box.set_child_non_homogeneous(self._attach_button, True)

    def check_login(self):
        # Check if user is registered
        if not is_registered():
            # Show dialogue
            title = "Kano Login"
            description = "You need to login to Kano World before sending information. \nDo you want to continue?"
            kdialog = KanoDialog(
                title, description,
                {
                    "CANCEL":
                    {
                        "return_value": 1
                    },
                    "OK":
                    {
                        "return_value": 0
                    }
                },
                parent_window=self
            )
            kdialog.dialog.set_keep_above(False)
            self.set_keep_above(False)
            rc = kdialog.run()
            if rc == 0:
                Gtk.main_iteration()
                run_cmd('/usr/bin/kano-login')

            self.set_keep_above(True)
            del kdialog
            while Gtk.events_pending():
                Gtk.main_iteration()
