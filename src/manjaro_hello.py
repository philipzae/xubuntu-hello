#!/usr/bin/env python3

import gettext
import gi
import json
import locale
import os
import subprocess
import sys
import webbrowser
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf

class ManjaroHello():
    def __init__(self):
        # App vars
        self.app = "manjaro-hello"

        # Path vars
        if os.path.basename(sys.argv[0]) == self.app:
            self.data_path = "/usr/share/" + self.app + "/data/"
            self.locale_path = "/usr/share/locale/"
            self.ui_path = "/usr/share/" + self.app + "/ui/"
            self.desktop_path = "/usr/share/applications/" + self.app + ".desktop"
        else:
            self.data_path = "data/"
            self.locale_path = "locale/"
            self.ui_path = "ui/"
            self.desktop_path = os.getcwd() + "/" + self.app + ".desktop"

        self.config_path = os.path.expanduser("~") + "/.config/"
        self.preferences_path = self.config_path + self.app + ".json"
        self.urls_path = self.data_path + "urls.json"
        self.autostart_path = self.config_path + "autostart/" + self.app + ".desktop"
        self.logo_path = "/usr/share/icons/manjaro.png"

        # Load preferences
        self.preferences = self.get_preferences()

        # Load system infos
        self.infos = get_infos()

        # Load data files
        self.urls = read_json(self.urls_path)

        # Init window
        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.ui_path + "manjaro-hello.glade")
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("window")

        # Load logos
        logo = GdkPixbuf.Pixbuf.new_from_file_at_scale(self.logo_path, 75, 75, False)
        self.window.set_icon_from_file(self.logo_path)
        self.builder.get_object("manjaroicon").set_from_pixbuf(logo)
        self.builder.get_object("aboutdialog").set_logo(logo)

        # Init translation
        self.default_locale = "en"
        self.sys_locale = locale.getdefaultlocale()[0]
        self.default_texts = {}
        locales = os.listdir(self.locale_path)
        locales.append(self.default_locale)
        # Choose best locale for user
        if self.preferences["locale"] not in locales:
            if self.sys_locale in locales:
                self.preferences["locale"] = self.sys_locale
            else:
                if self.sys_locale[:2] in locales:
                    self.preferences["locale"] = self.sys_locale[:2]
                else:
                    self.preferences["locale"] = self.default_locale

        # Select current locale in languages menu
        self.builder.get_object("languages").set_active_id(self.preferences["locale"]);
        self.builder.get_object("languages").connect("changed", self.on_languages_changed)

        # Make translation
        gettext.bindtextdomain(self.app, self.locale_path)
        gettext.textdomain(self.app)
        self.set_locale(self.preferences["locale"])

        # Save used locale in config file
        self.save_preferences()

        # Set window subtitle
        if self.infos["codename"] and self.infos["release"]:
            self.builder.get_object("headerbar").props.subtitle = self.infos["codename"] + " " + self.infos["release"] + " "
        self.builder.get_object("headerbar").props.subtitle += self.infos["arch"]

        # Load images
        for img in ("google+", "facebook", "twitter", "reddit"):
            self.builder.get_object(img).set_from_file(self.data_path + "img/" + img + ".png")

        # Set autostart switcher state
        self.builder.get_object("autostart").set_active(self.preferences["autostart"])

        # Live systems
        if self.infos["live"]:
            self.builder.get_object("installlabel").set_visible(True)
            if os.path.isfile("/usr/bin/calamares"):
                self.builder.get_object("installgui").set_visible(True)
            if os.path.isfile("/usr/bin/cli-installer"):
                self.builder.get_object("installcli").set_visible(True)

        self.window.show();

    def set_locale(self, locale):
        """Set locale of ui and pages.
        :param locale: locale to use
        :type locale: str
        """
        if self.preferences["locale"] != self.default_locale:
            tr = gettext.translation(self.app, self.locale_path, [locale])
            tr.install()
        else:
            gettext.install(self.app)

        # Dirty code to fix an issue with gettext that can't translate strings from glade files
        # Redfining all translatables strings
        # TODO: Find a better solution
        elts = {
            "welcometitle": "label",
            "welcomelabel": "label",
            "firstcategory": "label",
            "secondcategory": "label",
            "thirdcategory": "label",
            "readme": "label",
            "release": "label",
            "wiki": "label",
            "involved": "label",
            "forums": "label",
            "chat": "label",
            "mailling": "label",
            "build": "label",
            "donate": "label",
            "installlabel": "label",
            "installgui": "label",
            "installcli": "label",
            "autostartlabel": "label",
            "aboutdialog": "comments"
        }
        for elt in elts:
            if elt not in self.default_texts:
                self.default_texts[elt] = getattr(self.builder.get_object(elt), "get_" + elts[elt])()
            getattr(self.builder.get_object(elt), "set_" + elts[elt])(_(self.default_texts[elt]))

        # Load pages
        for page in ("readme", "release", "involved"):
            self.builder.get_object(page + "label").set_markup(self.read_page(page))

    def change_autostart(self, autostart):
        """Set state of autostart.
        :param autostart: wanted autostart state
        :type autostart: bool
        """
        try:
            if autostart and not os.path.isfile(self.autostart_path):
                os.symlink(self.desktop_path, self.autostart_path)
            elif not autostart and os.path.isfile(self.autostart_path):
                os.unlink(self.autostart_path)
        except OSError as e:
            print(e)
        self.preferences["autostart"] = autostart
        self.save_preferences()

    def save_preferences(self):
        """Save preferences in config file."""
        try:
            with open(self.preferences_path, "w") as f:
                json.dump(self.preferences, f)
        except OSError as e:
            print(e)

    def get_preferences(self):
        """Read preferences from config file."""
        preferences = read_json(self.preferences_path)
        if not preferences:
            preferences = {
                "autostart": os.path.isfile(self.autostart_path),
                "locale": None
            }
        return preferences

    def read_page(self, name):
        """Read page according to language.
        :param name: name of page (filename)
        :type name: str
        :return: text to load
        :rtype: str
        """
        filename = self.data_path + "pages/{}/{}".format(self.preferences["locale"], name)
        if not os.path.isfile(filename):
            filename = self.data_path + "pages/{}/{}".format(self.default_locale, name)
        try:
            with open(filename, "r") as f:
                return f.read()
        except OSError as e:
            return _("Can't load page.")

    # Handlers
    def on_languages_changed(self, combobox):
        """Event for selected language."""
        self.preferences["locale"] = combobox.get_active_id()
        self.set_locale(self.preferences["locale"])
        self.save_preferences()

    def on_action_clicked(self, action, _=None):
        """Event for differents actions."""
        name = action.get_name()
        if name == "installgui":
            subprocess.call(["sudo", "-E", "calamares"])
        elif name == "installcli":
            subprocess.call(["sudo cli-installer"])
        elif name == "autostart":
            autostart = True if action.get_active() else False
            self.change_autostart(autostart)
        elif name == "about":
            dialog = self.builder.get_object("aboutdialog")
            dialog.set_transient_for(self.window)
            dialog.run()
            dialog.hide()

    def on_btn_clicked(self, btn):
        """Event for clicked button."""
        self.builder.get_object("stack").set_visible_child(self.builder.get_object(btn.get_name() + "page"))

    def on_link_clicked(self, link, _=None):
        """Event for clicked link."""
        webbrowser.open_new_tab(self.urls[link.get_name()])

    def on_delete_window(self, *args):
        """Event to quit app."""
        Gtk.main_quit(*args)

def get_infos():
    """Get informations about user's system.
    :return: informations about user's system
    :rtype: dict
    """
    lsb = get_lsb_infos()
    infos = {}
    infos["codename"] = lsb.get("CODENAME", None)
    infos["release"] = lsb.get("RELEASE", None)
    infos["arch"] = "64-bits" if sys.maxsize > 2**32 else "32-bits"
    infos["live"] = os.path.exists("/bootmnt/manjaro") or os.path.exists("/run/miso/bootmnt/manjaro")
    return infos

def get_lsb_infos():
    """Read informations from the lsb-release file.
    :return: args from lsb-release file
    :rtype: dict
    """
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
    except OSError as e:
        print(e)
    return lsb

def read_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except OSError as e:
        return None

if __name__ == "__main__":
    ManjaroHello()
    Gtk.main()