#!/bin/sh
# Script to generate mo files in a locale folder
# Use it just only for testing purpose
rm -rf locale
mkdir locale
cd po
for lang in $(ls -1 | sed -e 's/\..*$//'); do
    if [ $lang != "manjaro-hello" ]
    then
        mkdir -p ../locale/$lang/LC_MESSAGES
        msgfmt -c -o ../locale/$lang/LC_MESSAGES/manjaro-hello.mo $lang.po
    fi
done
cd ..
python src/manjaro_hello.py
