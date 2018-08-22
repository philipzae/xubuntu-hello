#!/usr/bin/env python3

import collections
import glob
import urllib.request
import gettext
import json
import locale
import os
import subprocess
import sys
import webbrowser
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, GLib

# Applications class constants
VERSION = "0.8"
TITLE = "Manjaro Application Utility {}".format(VERSION)
GROUP = 0
ICON = 1
APPLICATION = 2
DESCRIPTION = 3
ACTIVE = 4
PACKAGE = 5
INSTALLED = 6


class Applications(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title=TITLE, border_width=6)
        self.app = "manjaro-hello"
        self.dev = "--dev" in sys.argv
        if self.dev:
            self.preferences = self.read_json_file("data/preferences.json".format(self.app))
        else:
            self.preferences = self.read_json_file("/usr/share/{}/data/preferences.json".format(self.app))
        self.preferences["data_path"] = "./data"
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        icon="system-software-install"
        pixbuf24 = Gtk.IconTheme.get_default().load_icon(icon, 24, 0)
        pixbuf32 = Gtk.IconTheme.get_default().load_icon(icon, 32, 0)
        pixbuf48 = Gtk.IconTheme.get_default().load_icon(icon, 48, 0)
        pixbuf64 = Gtk.IconTheme.get_default().load_icon(icon, 64, 0)
        pixbuf96 = Gtk.IconTheme.get_default().load_icon(icon, 96, 0)
        self.set_icon_list([pixbuf24, pixbuf32, pixbuf48, pixbuf64, pixbuf96])

        # set data
        self.app_store = None
        self.pkg_selected = None
        self.pkg_installed = None
        self.pkg_list_install = []
        self.pkg_list_removal = []

        # setup main box
        self.set_default_size(800, 650)
        self.application_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.application_box)

        # create title box
        self.title_box = Gtk.Box()
        self.title_image = Gtk.Image()
        self.title_image.set_size_request(100, 100)
        self.title_image.set_from_file("/usr/share/icons/manjaro/maia/96x96.png")
        self.title_label = Gtk.Label()
        self.title_label.set_markup("<big>Manjaro Application Maintenance</big>\n"
                                    "Select/Deselect apps you want to install/remove.\n"
                                    "Click <b>UPDATE SYSTEM</b> button when ready.")
        self.title_box.pack_start(self.title_image, expand=False, fill=False, padding=0)
        self.title_box.pack_start(self.title_label, expand=True, fill=True, padding=0)

        # pack title box to main box
        self.application_box.pack_start(self.title_box, expand=False, fill=False, padding=0)

        # setup grid
        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)
        self.application_box.add(self.grid)

        # setup list store model
        self.app_store = self.load_app_data(self.preferences["data_set"])

        # create a tree view with the model store
        self.tree_view = Gtk.TreeView.new_with_model(self.app_store)
        self.tree_view.set_activate_on_single_click(True)

        # column model: icon
        icon = Gtk.CellRendererPixbuf()
        column = Gtk.TreeViewColumn("", icon, icon_name=ICON)
        self.tree_view.append_column(column)

        # column model: group name column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Group", renderer, text=GROUP)
        self.tree_view.append_column(column)

        # column model: app name column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Application", renderer, text=APPLICATION)
        self.tree_view.append_column(column)

        # column model: description column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Description", renderer, text=DESCRIPTION)
        self.tree_view.append_column(column)

        # column model: install column
        toggle = Gtk.CellRendererToggle()
        toggle.connect("toggled", self.on_app_toggle)
        column = Gtk.TreeViewColumn("Installed", toggle, active=ACTIVE)
        self.tree_view.append_column(column)

        # button box
        self.button_box = Gtk.Box(spacing=10)
        self.advanced = Gtk.ToggleButton(label="Advanced")
        self.advanced.connect("clicked", self.on_expert_clicked)
        self.download = Gtk.Button(label="download")
        self.download.connect("clicked", self.on_download_clicked)
        self.reload_button = Gtk.Button(label="reload")
        self.reload_button.connect("clicked", self.on_reload_clicked)
        self.update_system_button = Gtk.Button(label="UPDATE SYSTEM")
        self.update_system_button.connect("clicked", self.on_update_system_clicked)
        self.close_button = Gtk.Button(label="close")
        self.close_button.connect("clicked", self.on_close_clicked)
        self.button_box.pack_start(self.advanced, expand=False, fill=False, padding=10)
        self.button_box.pack_end(self.update_system_button, expand=False, fill=False, padding=10)
        self.button_box.pack_end(self.close_button, expand=False, fill=False, padding=10)
        self.button_box.pack_end(self.reload_button, expand=False, fill=False, padding=10)
        self.button_box.pack_end(self.download, expand=False, fill=False, padding=10)
        self.application_box.pack_end(self.button_box, expand=False, fill=False, padding=10)

        # create a scrollable window
        self.app_window = Gtk.ScrolledWindow()
        self.app_window.set_vexpand(True)
        self.app_window.add(self.tree_view)
        self.grid.attach(self.app_window, 0, 0, 5, len(self.app_store))

        # show start
        self.show_all()

    def load_app_data(self, data_set):
        if os.path.isfile("{}/{}.json".format(self.preferences["user_path"], data_set)):
            app_data = self.read_json_file("{}/{}.json".format(self.preferences["user_path"], data_set))
        else:
            app_data = self.read_json_file("{}/{}.json".format(self.preferences["data_path"], data_set))

        store = Gtk.TreeStore(str, str, str, str, bool, str, bool)
        for group in app_data:
            index = store.append(None,
                                 [group["name"],
                                  group["icon"],
                                  None, group["description"], None, None, None])
            for app in group["apps"]:
                status = self.app_installed(app["pkg"])
                tree_item = (None,
                             app["icon"],
                             app["name"],
                             app["description"],
                             status,
                             app["pkg"],
                             status)
                store.append(index, tree_item)
        return store

    def reload_app_data(self, dataset):
        self.pkg_selected = None
        self.pkg_installed = None
        self.pkg_list_install = []
        self.pkg_list_removal = []
        self.app_store.clear()
        self.app_store = self.load_app_data(dataset)
        self.tree_view.set_model(self.app_store)

    def on_close_clicked(self, widget):
        self.hide()

    def on_reload_clicked(self, widget):
        self.reload_app_data(self.preferences["data_set"])

    def on_expert_clicked(self, widget):
        if widget.get_active():
            self.preferences["data_set"] = "advanced"
        else:
            self.preferences["data_set"] = "default"
        self.reload_app_data(self.preferences["data_set"])

    def on_download_clicked(self, widget):
        if self.net_check():
            # noinspection PyBroadException
            try:
                for download in self.preferences["data_sets"]:
                    url = "{}/{}.json".format(self.preferences["url"], download)
                    file = self.fix_path("{}/{}.json".format(self.preferences["user_path"], download))
                    req = urllib.request.Request(url=url)
                    with urllib.request.urlopen(req, timeout=2) as response:
                        data = json.loads(response.read().decode("utf8"))
                        self.write_json_file(data, file)

            except Exception as e:
                print(e)

        else:
            dialog = Gtk.MessageDialog(self, 0,
                                       Gtk.MessageType.ERROR,
                                       Gtk.ButtonsType.CANCEL,
                                       "Download not available")
            dialog.format_secondary.text("The server 'gitlab.manjaro.org' could not be reached")
            dialog.run()

    def on_app_toggle(self, cell, path):
        # a group has no package attached and we don't install groups
        if self.app_store[path][PACKAGE] is not None:
            self.app_store[path][ACTIVE] = not self.app_store[path][ACTIVE]
            self.pkg_selected = self.app_store[path][PACKAGE]
            self.pkg_installed = self.app_store[path][INSTALLED]

            if self.app_store[path][ACTIVE] is False:
                if self.pkg_installed is True:
                    # to uninstall
                    self.pkg_list_removal.append(self.pkg_selected)
                    if self.dev:
                        print("for removal   : {}".format(self.pkg_selected))
                if self.pkg_selected in self.pkg_list_install:
                    # cancel install
                    self.pkg_list_install.remove(self.pkg_selected)
                    if self.dev:
                        print("cancel install: {}".format(self.pkg_selected))
            else:
                # don't reinstall
                if self.pkg_installed is False:
                    # only install
                    if self.pkg_selected not in self.pkg_list_install:
                        self.pkg_list_install.append(self.pkg_selected)
                        if self.dev:
                            print("to install    : {}".format(self.pkg_selected))
                if self.pkg_selected in self.pkg_list_removal:
                    # cancel uninstall
                    self.pkg_list_removal.remove(self.pkg_selected)
            if self.dev:
                print("pkg list install: {}".format(self.pkg_list_install))
                print("pkg list removal: {}".format(self.pkg_list_removal))

    def on_update_system_clicked(self, widget):
        file_install = "/tmp/.install-packages.txt"
        file_uninstall = "/tmp/.remove-packages.txt"

        os.environ["APP_UTILITY"] = "PACKAGES"
        shell_fallback = False

        if self.pkg_list_install:
            if os.path.isfile("/usr/bin/pamac-installer"):
                subprocess.run(["pamac-installer"] + self.pkg_list_install)
            else:
                shell_fallback = True
                with open(file_install, "w") as outfile:
                    for p in self.pkg_list_install:
                        outfile.write("{} ".format(p))

        if self.pkg_list_removal:
            shell_fallback = True
            with open(file_uninstall, "w") as outfile:
                for p in self.pkg_list_removal:
                    outfile.write("{} ".format(p))

        if shell_fallback:
            if self.dev:
                os.system('gksu-polkit ./app-install')
            else:
                os.system('gksu-polkit app-install')

        self.reload_app_data(self.preferences["data_set"])

    @staticmethod
    def app_installed(package):
        if glob.glob("/var/lib/pacman/local/{}-[0-9]*".format(package)):
            return True
        return False

    @staticmethod
    def fix_path(path):
        """Make good paths.
        :param path: path to fix
        :type path: str
        :return: fixed path
        :rtype: str
        """
        if "~" in path:
            path = path.replace("~", os.path.expanduser("~"))
        return path

    @staticmethod
    def net_check():
        """Check for internet connection"""
        resp = None
        host = "https://gitlab.manjaro.org"
        # noinspection PyBroadException
        try:
            resp = urllib.request.urlopen(host, timeout=2)
        except Exception:
            pass
        return bool(resp)

    @staticmethod
    def read_json_file(filename, dictionary=True):
        """Read json data from file"""
        result = list()
        try:
            if dictionary:
                with open(filename, "rb") as infile:
                    result = json.loads(
                        infile.read().decode("utf8"),
                        object_pairs_hook=collections.OrderedDict)
            else:
                with open(filename, "r") as infile:
                    result = json.load(infile)
        except OSError:
            pass
        return result

    @staticmethod
    def write_json_file(data, filename, dictionary=False):
        """Writes data to file as json
        :param data
        :param filename:
        :param dictionary:
        """
        try:
            if dictionary:
                with open(filename, "wb") as outfile:
                    json.dump(data, outfile)
            else:
                with open(filename, "w") as outfile:
                    json.dump(data, outfile, indent=2)
            return True
        except OSError:
            return False


class Hello(Gtk.Window):
    """Hello"""

    def __init__(self):
        Gtk.Window.__init__(self, title="Manjaro Hello", border_width=6)
        self.app = "manjaro-hello"
        self.dev = "--dev" in sys.argv  # Dev mode activated ?

        # used by application utility
        self.app_store = None
        self.pkg_selected = None
        self.pkg_installed = None
        self.pkg_list_install = []
        self.pkg_list_removal = []

        # Load preferences
        if self.dev:
            self.preferences = read_json("data/preferences.json")
            self.preferences["data_path"] = "data/"
            self.preferences["desktop_path"] = os.getcwd() + "/{}.desktop".format(self.app)
            self.preferences["locale_path"] = "locale/"
            self.preferences["ui_path"] = "ui/{}.glade".format(self.app)
        else:
            self.preferences = read_json("/usr/share/{}/data/preferences.json".format(self.app))

        # Get saved infos
        self.save = read_json(self.preferences["save_path"])
        if not self.save:
            self.save = {"locale": None}

        # Init window
        self.builder = Gtk.Builder.new_from_file(self.preferences["ui_path"])
        self.builder.connect_signals(self)
        self.window = self.builder.get_object("window")

        # Subtitle of headerbar
        self.builder.get_object("headerbar").props.subtitle = ' '.join(get_lsb_infos())

        # Load images
        if os.path.isfile(self.preferences["logo_path"]):
            logo = GdkPixbuf.Pixbuf.new_from_file(self.preferences["logo_path"])
            self.window.set_icon(logo)
            self.builder.get_object("distriblogo").set_from_pixbuf(logo)
            self.builder.get_object("aboutdialog").set_logo(logo)

        for btn in self.builder.get_object("social").get_children():
            icon_path = self.preferences["data_path"] + "img/" + btn.get_name() + ".png"
            self.builder.get_object(btn.get_name()).set_from_file(icon_path)

        for widget in self.builder.get_object("homepage").get_children():
            if isinstance(widget, Gtk.Button) and \
               widget.get_image_position() is Gtk.PositionType.RIGHT:
                img = Gtk.Image.new_from_file(
                    self.preferences["data_path"] + "img/external-link.png")
                img.set_margin_left(2)
                widget.set_image(img)

        # Create pages
        self.pages = os.listdir("{}/pages/{}".format(self.preferences["data_path"],
                                                     self.preferences["default_locale"]))
        for page in self.pages:
            scrolled_window = Gtk.ScrolledWindow()
            viewport = Gtk.Viewport(border_width=10)
            label = Gtk.Label(wrap=True)
            viewport.add(label)
            scrolled_window.add(viewport)
            scrolled_window.show_all()
            self.builder.get_object("stack").add_named(scrolled_window, page + "page")

        # Init translation
        self.default_texts = {}
        gettext.bindtextdomain(self.app, self.preferences["locale_path"])
        gettext.textdomain(self.app)
        self.builder.get_object("languages").set_active_id(self.get_best_locale())

        # Set autostart switcher state
        self.autostart = os.path.isfile(fix_path(self.preferences["autostart_path"]))
        self.builder.get_object("autostart").set_active(self.autostart)

        # Live systems
        if os.path.exists(self.preferences["live_path"]) and \
           os.path.isfile(self.preferences["installer_path"]):
            self.builder.get_object("installlabel").set_visible(True)
            self.builder.get_object("install").set_visible(True)
        else:
            self.builder.get_object("applications").set_visible(True)

        self.window.show()

    def get_best_locale(self):
        """Choose best locale, based on user's preferences.
        :return: locale to use
        :rtype: str
        """
        path = self.preferences["locale_path"] + "{}/LC_MESSAGES/" + self.app + ".mo"
        if os.path.isfile(path.format(self.save["locale"])):
            return self.save["locale"]
        elif self.save["locale"] == self.preferences["default_locale"]:
            return self.preferences["default_locale"]
        else:
            sys_locale = locale.getdefaultlocale()[0]
            # If user's locale is supported
            if os.path.isfile(path.format(sys_locale)):
                if "_" in sys_locale:
                    return sys_locale.replace("_", "-")
                else:
                    return sys_locale
            # If two first letters of user's locale is supported (ex: en_US -> en)
            elif os.path.isfile(path.format(sys_locale[:2])):
                return sys_locale[:2]
            else:
                return self.preferences["default_locale"]

    def set_locale(self, locale):
        """Set locale of ui and pages.
        :param locale: locale to use
        :type locale: str
        """
        try:
            translation = gettext.translation(self.app, self.preferences[
                "locale_path"], [locale], fallback=True)
            translation.install()
        except OSError:
            return

        self.save["locale"] = locale

        # Real-time locale changing

        elts = {
            "comments": { "aboutdialog"},
            "label": {
                "autostartlabel",
                "development",
                "chat",
                "donate",
                "firstcategory",
                "forum",
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
                "home",
                "development",
                "chat",
                "donate",
                "forum",
                "mailling",
                "wiki"
            }
        }
        for method in elts:
            if method not in self.default_texts:
                self.default_texts[method] = {}
            for elt in elts[method]:
                if elt not in self.default_texts[method]:
                    self.default_texts[method][elt] = getattr(
                        self.builder.get_object(elt), "get_" + method)()
                getattr(self.builder.get_object(elt), "set_" + method)(_(self.default_texts[method][elt]))

        # Change content of pages
        for page in self.pages:
            child = self.builder.get_object("stack").get_child_by_name(page + "page")
            label = child.get_children()[0].get_children()[0]
            label.set_markup(self.get_page(page))

    def set_autostart(self, autostart):
        """Set state of autostart.
        :param autostart: wanted autostart state
        :type autostart: bool
        """
        try:
            if autostart and not os.path.isfile(fix_path(self.preferences["autostart_path"])):
                os.symlink(self.preferences["desktop_path"],
                           fix_path(self.preferences["autostart_path"]))
            elif not autostart and os.path.isfile(fix_path(self.preferences["autostart_path"])):
                os.unlink(fix_path(self.preferences["autostart_path"]))
            # Specific to i3
            i3_config = fix_path("~/.i3/config")
            if os.path.isfile(i3_config):
                i3_autostart = "exec --no-startup-id " + self.app
                with open(i3_config, "r+") as fil:
                    content = fil.read()
                    fil.seek(0)
                    if autostart:
                        fil.write(content.replace("#" + i3_autostart, i3_autostart))
                    else:
                        fil.write(content.replace(i3_autostart, "#" + i3_autostart))
                    fil.truncate()
            self.autostart = autostart
        except OSError as error:
            print(error)

    def get_page(self, name):
        """Read page according to language.
        :param name: name of page (filename)
        :type name: str
        :return: text to load
        :rtype: str
        """
        filename = self.preferences["data_path"] + "pages/{}/{}".format(self.save["locale"], name)
        if not os.path.isfile(filename):
            filename = self.preferences["data_path"] + \
                "pages/{}/{}".format(self.preferences["default_locale"], name)
        try:
            with open(filename, "r") as fil:
                return fil.read()
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
            subprocess.Popen(["calamares_polkit"])
        elif name == "autostart":
            self.set_autostart(action.get_active())
        elif name == "about":
            dialog = self.builder.get_object("aboutdialog")
            dialog.run()
            dialog.hide()
        elif name == "applications":
            win = Applications()
            win.show_all()

    def on_btn_clicked(self, btn):
        """Event for clicked button."""
        name = btn.get_name()
        print(name)
        self.builder.get_object("home").set_sensitive(not name == "home")
        self.builder.get_object("stack").set_visible_child_name(name + "page")

    def on_link_clicked(self, link, _=None):
        """Event for clicked link."""
        webbrowser.open_new_tab(self.preferences["urls"][link.get_name()])

    def on_delete_window(self, *args):
        """Event to quit app."""
        write_json(self.preferences["save_path"], self.save)
        Gtk.main_quit(*args)


def fix_path(path):
    """Make good paths.
    :param path: path to fix
    :type path: str
    :return: fixed path
    :rtype: str
    """
    if "~" in path:
        path = path.replace("~", os.path.expanduser("~"))
    return path


def read_json(path):
    """Read content of a json file.
    :param path: path to read
    :type path: str
    :return: json content
    :rtype: str
    """
    path = fix_path(path)
    try:
        with open(path, "r") as fil:
            return json.load(fil)
    except OSError:
        return None


def write_json(path, content):
    """Write content in a json file.
    :param path: path to write
    :type path: str
    :param content: content to write
    :type path: str
    """
    path = fix_path(path)
    try:
        with open(path, "w") as fil:
            json.dump(content, fil)
    except OSError as error:
        print(error)


def get_lsb_infos():
    """Read informations from the lsb-release file.
    :return: args from lsb-release file
    :rtype: dict"""
    lsb = {}
    try:
        with open("/etc/lsb-release") as fil:
            for line in fil:
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
    return lsb["CODENAME"], lsb["RELEASE"]


if __name__ == "__main__":
    hello = Hello()
    hello.connect("destroy", Gtk.main_quit)
    Gtk.main()
