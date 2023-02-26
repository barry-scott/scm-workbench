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

Linux-Ubuntu|Linux-Debian)
    . /etc/os-release
    TARGET=/shared/Downloads/ScmWorkbench/beta/${VERSION_CODENAME}
    mkdir -p ${TARGET}
    for DEB in tmp/*.deb
    do
        if [[ -e "$DEB" ]]
        then
            cp -v "$DEB" ${TARGET}
        else
            colour-print "<>error Error: No .deb file found<>"
        fi
    done
    if [[ "$1" = "--install" ]]
    then
        pushd /shared/Downloads/Debian
        ./make-apt-repos.sh update ${VERSION_CODENAME}

        colour-print "<>info Info: apt update<>"
        sudo apt update

        colour-print "<>info Info: apt install<>"
        sudo apt install scm-workbench
    fi
    ;;

*)
    echo "Unsupported platform for copy"
    ;;
esac
