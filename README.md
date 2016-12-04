manjaro-hello
=============

New Manjaro Welcome Screen

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/4c5342caee874c079638970437d49196)](https://www.codacy.com/app/hugo-posnic/manjaro-hello?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Huluti/manjaro-hello&amp;utm_campaign=Badge_Grade)

## Why a new Manjaro Welcome Screen ?

Manjaro-hello is widely inspired by [manjaro-welcome](https://github.com/manjaro/manjaro-welcome). I've started to work on a new welcome screen because I think that the current has several defects inherited from the technologies used.
- First, it is based on Gtk3 but because of the use of Webkit and its old Python binding, it is forced to use Gtk2.
- All the app content is displayed by using HTML that is rendered by Webkit. This makes the evolution of the software very complicated. For example, it is very hard to make a translation system.
- By using web technologies and Webkit, the renderer is a little bit slower than using native technologies.

For all this reasons, I have choosen to build a new software from scratch  but keeping the original structure.

Currently, manjaro-hello has all the major features of manjaro-welcome but have a translation system.
- Interface is translated using gettext and po files. (src/locale)
- Pages are translated using differents files. (src/data)

## What goals ?

The first goal of the project is to build a powerful welcome screen who welcome the new user and help him to discover our favorite distribution :).

Finnaly, the second goal is to push it to replace the original project.

## Technologies

Manjaro-hello is build with Python, Gtk3 and Glade.

## TODO

For the moment, even if the soft works, it is not finished.
- We have to test it and fix bugs.
- Make translations to distribute it in all the world.
- Improve way to render pages. (use a Markdown-like system ?)
- Improve the look (manjaro-welcome is very great-looking).

Let's make a wonderful software !
