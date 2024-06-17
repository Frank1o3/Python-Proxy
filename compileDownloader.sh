#!/bin/bash

if [ -e "$(pwd)/Downloader.exe" ]; then
    rm -r Downloader.exe
fi

shc -f Downloader.sh

x86_64-w64-mingw32-gcc Downloader.sh.x.c -o Downloader.exe

rm -r Downloader.sh.x

rm -r Downloader.sh.x.c