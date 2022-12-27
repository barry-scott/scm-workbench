#!/bin/bash
case "${BUILDER_CFG_PLATFORM}" in
MacOSX)
    DMG=$( echo tmp/dmg/*.dmg )
    if [ ! -e /Volumes/Downloads ]
    then
        echo "Mounting shares..."
        open -a mount-shares
    fi

    for ((i=1; i<=120; i++))
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

Linux-Ubuntu)
    DEB=$( echo tmp/*.deb )
    if [[ -e "$DEB" ]]
    then
        cp -v "$DEB" /shared/Downloads/ScmWorkbench/beta
    else
        colour-print "<>error Error: No .deb file found<>"
    fi
    ;;

*)
    echo "Unsupported platform for copy"
    ;;
esac
