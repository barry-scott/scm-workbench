#!/bin/echo Usage: . $0

export BUILDER_CFG_PLATFORM=$(uname -s)
export PYTHON_VERSION=${1:-3.5}
case ${BUILDER_CFG_PLATFORM} in

Darwin)
    export BUILDER_CFG_PLATFORM=MacOSX
    export PYTHON=python${PYTHON_VERSION}
    export BUILDER_QTDIR=$HOME/Qt-5.7.0/5.7
    ;;

Linux)
    for version in ${PYTHON_VERSION} 3.4
    do
        if [ -e /usr/bin/python${version} ]
        then
            export PYTHON_VERSION=${version}
            break
        fi
    done
    if [ -e /etc/fedora-release ]
    then
        export BUILDER_CFG_PLATFORM=Linux-Fedora

    elif [ -e /etc/lsb-release ]
    then
        if [ "$( grep "DISTRIB_ID=Ubuntu" /etc/lsb-release )" = "DISTRIB_ID=Ubuntu" ]
        then
            export BUILDER_CFG_PLATFORM=Linux-Ubuntu
        fi

    elif [ -e /etc/os-release ]
    then
        if [ "$( grep "ID=debian" /etc/os-release )" = "ID=debian" ]
        then
            export BUILDER_CFG_PLATFORM=Linux-Debian
        fi
    fi
    export PYTHON=python${PYTHON_VERSION}
    ;;
*)
    # no need to change
    ;;
esac

echo Info: WorkingDir: ${BUILDER_TOP_DIR}
echo Info: Config Platform: ${BUILDER_CFG_PLATFORM}
echo Info: Python Version: ${PYTHON_VERSION}
