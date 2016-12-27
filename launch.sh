#!/bin/sh
# Script to generate mo files in a temp locale folder
# Use it only for testing purpose
rm -rf locale
mkdir locale
cd po
for lang in $(ls *.po); do
    mkdir -p ../locale/${lang::-3}/LC_MESSAGES
    msgfmt -c -o ../locale/${lang::-3}/LC_MESSAGES/manjaro-hello.mo $lang
done
cd ..
python src/manjaro_hello.py
