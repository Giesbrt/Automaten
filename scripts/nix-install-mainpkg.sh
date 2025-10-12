#!/usr/bin/env bash
rm -f ../src/app/default-config/config/extra-libs/mainpkg
ln -s "$(realpath ../src/mainpkg)" ../src/app/default-config/config/extra-libs/mainpkg
ls -l ../src/app/default-config/config/extra-libs/mainpkg
echo Press ENTER to exit ...
read
