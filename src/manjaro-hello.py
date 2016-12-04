#!/usr/bin/env python3

import locale
import gettext
import os
import sys
import json
import gi
import shutil
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GdkPixbuf

class ManjaroHello(Gtk.Window):
    def __init__(self):
        self.preferences_path = "{}/.config/manjaro-hello.json".format(os.path.expanduser("~"))
        self.autostart_path = os.path.expanduser("{}/.config/autostart/manjaro-hello.desktop".format(os.path.expanduser("~")))
        self.icon_path = "manjaro-hello.png"

        self.language = locale.getlocale()[0][:2]
        self.default_language = "en"
        self.app = "manjaro-hello"
        self.locale_dir = "locale"

        self.preferences = self.get_preferences()
        if not self.preferences:
            self.preferences = {"autostart": os.path.exists(self.autostart_path)}
            self.save_preferences()

        self.infos = self.get_infos()

        # Init language
        locale.setlocale(locale.LC_ALL, "")
        locale.bindtextdomain(self.app, self.locale_dir)
        gettext.bindtextdomain(self.app, self.locale_dir)
        gettext.textdomain(self.app)

        # Create window
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(self.app)
        self.builder.add_from_file("manjaro-hello.glade")
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("window")

        self.builder.get_object("headerbar").props.subtitle = self.infos["codename"] + " " + self.infos["release"] + " " + self.infos["arch"]

        text_buffer = Gtk.TextBuffer()
        text_buffer.set_text(self.read_data("readme"), -1)
        self.builder.get_object("readmetext").set_buffer(text_buffer)

        text_buffer = Gtk.TextBuffer()
        text_buffer.set_text(self.read_data("release"), -1)
        self.builder.get_object("releasetext").set_buffer(text_buffer)

        text_buffer = Gtk.TextBuffer()
        text_buffer.set_text(self.read_data("involved"), -1)
        self.builder.get_object("involvedtext").set_buffer(text_buffer)

        self.builder.get_object("autostart").set_active(self.preferences["autostart"])

        self.window.show()

    def get_lsb_information(self):
        lsb = {}
        try:
            with open("/etc/lsb-release") as lsb_file:
                for line in lsb_file:
                    if "=" in line:
                        var, arg = line.rstrip().split("=")
                        if var.startswith("DISTRIB_"):
                            var = var[8:]
                        if arg.startswith("\"") and arg.endswith("\""):
                            arg = arg[1:-1]
                        if arg:
                            lsb[var] = arg
        except (IOError, OSError) as msg:
            print(msg)

        return lsb

    def get_infos(self):
        lsb = self.get_lsb_information()
        infos = {}
        infos["codename"] = lsb.get("CODENAME", 0)
        infos["release"] = lsb.get("RELEASE", 0)
        infos["arch"] = "64-bit" if os.uname()[4] else "32-bit"
        infos["live"] = os.path.exists("/bootmnt/manjaro") or os.path.exists("/run/miso/bootmnt/manjaro")

        return infos

    def change_autostart(self, state):
        if state and not os.path.exists(self.autostart_path):
            try:
                shutil.copyfile("manjaro-hello.desktop", self.autostart_path)
                self.preferences["autostart"] = True
            except (IOError, OSError) as e:
                print(e)
        elif not state and os.path.exists(self.autostart_path):
            try:
                os.remove(self.autostart_path)
                self.preferences["autostart"] = False
            except (IOError, OSError) as e:
                print(e)
        self.save_preferences()

    def save_preferences(self):
        try:
            with open(self.preferences_path, "w") as f:
                json.dump(self.preferences, f)
        except (IOError, OSError) as e:
            print(e)

    def get_preferences(self):
        try:
            with open(self.preferences_path, "r") as f:
                return json.load(f)
        except (IOError, OSError) as e:
            return None

    def read_data(self, name):
        filename = "data/{}/{}".format(self.language, name)
        if not os.path.exists(filename):
            filename = "data/{}/{}".format(self.default_language, name)

        try:
            with open(filename, "r") as f:
                return f.read()
        except (IOError, OSError) as e:
            return None

    # Handlers
    def on_about_clicked(self, btn):
        dialog = self.builder.get_object("aboutdialog")
        dialog.set_transient_for(self.window)
        dialog.run()
        dialog.hide()

    def on_readme_clicked(self, btn):
        self.builder.get_object("stack").set_visible_child(self.builder.get_object("documentation"))
        self.builder.get_object("documentation").set_current_page(0)

    def on_release_clicked(self, btn):
        self.builder.get_object("stack").set_visible_child(self.builder.get_object("documentation"))
        self.builder.get_object("documentation").set_current_page(1)

    def on_involved_clicked(self, btn):
        self.builder.get_object("stack").set_visible_child(self.builder.get_object("project"))
        self.builder.get_object("project").set_current_page(0)

    def on_autostart_switched(self, switch, _):
        autostart = True if switch.get_active() else False
        self.change_autostart(autostart)

    def on_delete_window(self, *args):
        Gtk.main_quit(*args)

win = ManjaroHello()
Gtk.main()
