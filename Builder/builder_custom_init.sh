#!/bin/echo Usage: . $0

export BUILDER_CFG_PLATFORM=$(uname -s)
case ${BUILDER_CFG_PLATFORM} in

Darwin)
    export PYTHON_VERSION=${1:-3.9}
    export BUILDER_CFG_PLATFORM=MacOSX
    export PYTHON=python${PYTHON_VERSION}
    ;;

Linux)
    export PYTHON_VERSION=${1:-3.9}

    for version in ${PYTHON_VERSION} 3.9 3.8 3.7 3.6 3.5 3.4
    do
        if [ -e /usr/bin/python${version} ]
        then
            export PYTHON_VERSION=${version}
            export PYTHON=/usr/bin/python${version}
            break

        elif [ -e /opt/rh/rh-python35/root/usr/bin/python${version} ]
        then
            export PYTHON_VERSION=${version}
            export PYTHON=/opt/rh/rh-python35/root/usr/bin/python${version}
        fi
    done
    if [ -e /etc/fedora-release ]
    then
        export BUILDER_CFG_PLATFORM=Linux-Fedora

    elif [ -e /etc/centos-release ]
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
    ;;
*)
    export PYTHON_VERSION=${1:-3.9}
    # no need to change
    ;;
esac

echo Info: WorkingDir: ${BUILDER_TOP_DIR}
echo Info: Config Platform: ${BUILDER_CFG_PLATFORM}
echo Info: Python Version: ${PYTHON_VERSION}
