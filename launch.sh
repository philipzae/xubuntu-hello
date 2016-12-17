# Use it just for local tests
rm -rf locale
mkdir locale
cd po
for lang in $(ls -1 | sed -e 's/\..*$//')
do
    if [ $lang != "manjaro-hello" ]
    then
        mkdir -p ../locale/$lang/LC_MESSAGES
        msgfmt -c -o ../locale/$lang/LC_MESSAGES/manjaro-hello.mo $lang.po
    fi
done
cd ../src
python manjaro-hello.py
