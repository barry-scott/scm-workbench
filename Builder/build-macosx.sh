#!/bin/bash
echo "Info: build-macosx.sh Builder - start"
make -f macosx.mak PYTHON=$PYTHON clean build 2>&1 | tee build.log

if /usr/bin/false
then
    echo "Info: rebuild the OS X launch service database"
    CORE=/System/Library/Frameworks/CoreServices.framework/Versions/Current
    ${CORE}/Frameworks/LaunchServices.framework/Versions/Current/Support/lsregister \
     -kill \
     -r -domain local -domain system -domain user 
fi

find .. -name '*.dmg'
echo "Info: build-macosx.sh Builder - end"
