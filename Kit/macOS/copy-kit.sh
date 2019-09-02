#!/bin/bash
case "${BUILDER_CFG_PLATFORM}" in
MacOSX)
    DMG=$( echo dmg.tmp/*.dmg )
    if [ ! -e /Volumes/Downloads ]
    then
        echo "Mounting shares..."
        open -a mount-shares
    fi

    for ((i=1; i<=30; i++))
    do
        if [ -e /Volumes/Downloads/ScmWorkbench/beta ]
        then
            cp -fv "$DMG" /Volumes/Downloads/ScmWorkbench/beta
            exit $?
        else
            sleep 1
        fi
    done
    echo "Downloads is missing"
    ;;

*)
    echo "Unsupported platform for copy"
    ;;
esac
