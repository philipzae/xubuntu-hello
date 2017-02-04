manjaro-hello
=============

A tool providing access to documentation and support for new Manjaro users.

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/4c5342caee874c079638970437d49196)](https://www.codacy.com/app/hugo-posnic/manjaro-hello?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Huluti/manjaro-hello&amp;utm_campaign=Badge_Grade)

## Why a new Manjaro Welcome Screen ?

Manjaro-hello is widely inspired by [manjaro-welcome](https://github.com/manjaro/manjaro-welcome). Manjaro-welcome has several defects, some of which are inherited from the technologies used:
- It is based on Gtk3 but because of the use of the old Python binding of Webkit, it is blocked on gtk2.
- The old old Python binding of Webkit has many serious security holes.
- Content of the app is displayed with web technologies. This makes the soft slower and complicates its evolution.
- Can't know if each link will be open in an external browser or in app.

For all this reasons, we have chosen to build a new software from scratch but keeping the original structure.

Currently, manjaro-hello has all the major features of manjaro-welcome plus a translation system.
- Interface is translated using gettext and po files. (po/)
- Pages are translated using differents files. (data/pages)

## What goals ?

The goal of the project is to build a powerful welcome screen who welcome the new user and help him to discover our favorite distribution :).

## Technologies

Manjaro-hello is build with Python, Gtk3 and Glade.

## TODO

- Make more translations to distribute it in all the world.

## Links

- [Discussion from Manjaro's forum](https://forum.manjaro.org/t/start-work-on-a-new-welcome-screen-for-manjaro/13685)
- [Translation project for Manjaro-Hello](https://www.transifex.com/manjarolinux/manjaro-hello)

Let's make a wonderful software !
