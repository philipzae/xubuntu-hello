#!/bin/sh
# Script to generate mo files in a temp locale folder
# Use it only for testing purpose
rm -rf locale
mkdir locale
cd po
for lang in $(ls *.po); do
    lang=${lang::-3}
    mkdir -p ../locale/${lang//_/-}/LC_MESSAGES
    msgfmt -c -o ../locale/${lang//_/-}/LC_MESSAGES/manjaro-hello.mo $lang.po
done
cd ..
python src/manjaro_hello.py
