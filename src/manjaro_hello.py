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
    """Manjaro-Hello"""

    def __init__(self):
        # App vars
        self.app = "manjaro-hello"

        # Path vars
        self.home_path = os.path.expanduser("~")
        self.logo_path = "/usr/share/icons/manjaro/maia/64x64.png"
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
        self.config_path = self.home_path + "/.config/"
        self.preferences_path = self.config_path + self.app + ".json"
        self.urls_path = self.data_path + "urls.json"
        self.autostart_path = self.config_path + "autostart/" + self.app + ".desktop"

        # Load preferences
        self.preferences = self.get_preferences()

        # Load system infos
        self.infos = get_infos()

        # Load data files
        self.urls = read_json(self.urls_path)

        # Init window
        self.builder = Gtk.Builder.new_from_file(self.ui_path + self.app + ".glade")
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("window")
        subtitle = self.infos["arch"]
        if self.infos["codename"] and self.infos["release"]:
            subtitle = self.infos["codename"] + " " + self.infos["release"] + " " + subtitle
        self.builder.get_object("headerbar").props.subtitle = subtitle

        # Load logo
        logo = GdkPixbuf.Pixbuf.new_from_file(self.logo_path)
        self.window.set_icon(logo)
        self.builder.get_object("manjaroicon").set_from_pixbuf(logo)
        self.builder.get_object("aboutdialog").set_logo(logo)

        # Create pages
        self.pages = ("readme", "release", "involved")
        for page in self.pages:
            scrolled_window = Gtk.ScrolledWindow()
            viewport = Gtk.Viewport(border_width=10)
            label = Gtk.Label(wrap=True)
            viewport.add(label)
            scrolled_window.add(viewport)
            scrolled_window.show_all()
            self.builder.get_object("stack").add_named(scrolled_window, page + "page")

        # Init translation
        self.default_locale = "en"
        self.default_texts = {}

        # Make translation
        gettext.bindtextdomain(self.app, self.locale_path)
        gettext.textdomain(self.app)
        self.builder.get_object("languages").set_active_id(self.get_best_locale())

        # Load images
        for img in ("google+", "facebook", "twitter", "reddit"):
            self.builder.get_object(img).set_from_file(self.data_path + "img/" + img + ".png")

        for btn in ("wiki", "forums", "chat", "mailling", "development", "donate"):
            img = Gtk.Image.new_from_file(self.data_path + "img/external-link.png")
            img.set_margin_left(2)
            self.builder.get_object(btn).set_image(img)

        # Set autostart switcher state
        self.autostart = os.path.isfile(self.autostart_path)
        self.builder.get_object("autostart").set_active(self.autostart)

        # Live systems
        if self.infos["live"] and os.path.isfile("/usr/bin/calamares"):
            self.builder.get_object("installlabel").set_visible(True)
            self.builder.get_object("install").set_visible(True)

        self.window.show()

    def get_best_locale(self):
        """Choose best locale, based on user's preferences.
        :return: locale to use
        :rtype: str
        """
        path = self.locale_path + "{}/LC_MESSAGES/" + self.app + ".mo"
        if os.path.isfile(path.format(self.preferences["locale"])):
            return self.preferences["locale"]
        else:
            sys_locale = locale.getdefaultlocale()[0]
            # If user's locale is supported
            if os.path.isfile(path.format(sys_locale)):
                return sys_locale
            # If two first letters of user's locale is supported (ex: en_US -> en)
            elif os.path.isfile(path.format(sys_locale[:2])):
                return sys_locale[:2]
            else:
                return self.default_locale

    def set_locale(self, locale):
        """Set locale of ui and pages.
        :param locale: locale to use
        :type locale: str
        """
        if "_" in locale:
            locale = locale.replace("_", "-")
        try:
            tr = gettext.translation(self.app, self.locale_path, [locale], fallback=True)
            tr.install()
        except OSError:
            return

        # Dirty code to fix an issue with gettext that can't translate strings from glade files
        # Redfining all translatables strings
        # TODO: Find a better solution
        elts = {
            "comments": {
                "aboutdialog"
            },
            "label": {
                "autostartlabel",
                "development",
                "chat",
                "donate",
                "firstcategory",
                "forums",
                "install",
                "installlabel",
                "involved",
                "mailling",
                "readme",
                "release",
                "secondcategory",
                "thirdcategory",
                "welcomelabel",
                "welcometitle",
                "wiki"
            },
            "tooltip_text": {
                "about",
                "home"
            }
        }
        for method in elts:
            for elt in elts[method]:
                if elt not in self.default_texts:
                    self.default_texts[elt] = getattr(self.builder.get_object(elt), "get_" + method)()
                getattr(self.builder.get_object(elt), "set_" + method)(_(self.default_texts[elt]))

        # Change content of pages
        for page in self.pages:
            child = self.builder.get_object("stack").get_child_by_name(page + "page")
            label = child.get_children()[0].get_children()[0]
            label.set_markup(self.get_page(page))

        self.preferences["locale"] = locale

    def set_autostart(self, autostart):
        """Set state of autostart.
        :param autostart: wanted autostart state
        :type autostart: bool
        """
        try:
            if autostart and not os.path.isfile(self.autostart_path):
                os.symlink(self.desktop_path, self.autostart_path)
            elif not autostart and os.path.isfile(self.autostart_path):
                os.unlink(self.autostart_path)
            # Specific to i3
            i3_config = self.home_path + "/.i3/config"
            if os.path.isfile(i3_config):
                i3_autostart = "exec --no-startup-id " + self.app
                with open(i3_config, "r+") as f:
                    content = f.read()
                    f.seek(0)
                    if autostart:
                        f.write(content.replace("#" + i3_autostart, i3_autostart))
                    else:
                        f.write(content.replace(i3_autostart, "#" + i3_autostart))
                    f.truncate()
            self.autostart = autostart
        except OSError as error:
            print(error)

    def save_preferences(self):
        """Save preferences in config file."""
        try:
            with open(self.preferences_path, "w") as f:
                json.dump(self.preferences, f)
        except OSError as error:
            print(error)

    def get_preferences(self):
        """Read preferences from config file."""
        preferences = read_json(self.preferences_path)
        if not preferences:
            preferences = {"locale": None}
        return preferences

    def get_page(self, name):
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
        except OSError:
            return _("Can't load page.")

    # Handlers
    def on_languages_changed(self, combobox):
        """Event for selected language."""
        self.set_locale(combobox.get_active_id())

    def on_action_clicked(self, action, _=None):
        """Event for differents actions."""
        name = action.get_name()
        if name == "install":
            subprocess.Popen(["pkexec", "calamares"])
        elif name == "autostart":
            self.set_autostart(action.get_active())
        elif name == "about":
            dialog = self.builder.get_object("aboutdialog")
            dialog.run()
            dialog.hide()

    def on_btn_clicked(self, btn):
        """Event for clicked button."""
        name = btn.get_name()
        self.builder.get_object("home").set_sensitive(not name == "home")
        self.builder.get_object("stack").set_visible_child_name(name + "page")

    def on_link_clicked(self, link, _=None):
        """Event for clicked link."""
        webbrowser.open_new_tab(self.urls[link.get_name()])

    def on_delete_window(self, *args):
        """Event to quit app."""
        self.save_preferences()
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
        with open("/etc/lsb-release") as f:
            for line in f:
                if "=" in line:
                    var, arg = line.rstrip().split("=")
                    if var.startswith("DISTRIB_"):
                        var = var[8:]
                    if arg.startswith("\"") and arg.endswith("\""):
                        arg = arg[1:-1]
                    if arg:
                        lsb[var] = arg
    except OSError as error:
        print(error)
    return lsb


def read_json(path):
    """Read content of a json file.
    :return: json content
    :rtype: str
    """
    try:
        with open(path, "r") as f:
            return json.load(f)
    except OSError:
        return None


if __name__ == "__main__":
    ManjaroHello()
    Gtk.main()
