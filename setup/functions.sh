#
# Common shell functions for os specific setup scripts.
#

detect_linux_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "${ID}${VERSION_ID}"
    elif [ -f /etc/redhat-release ]; then
        case `cat /etc/redhat-release` in
            'CentOS release 5.'*) echo "centos5" ;;
            'CentOS release 6.'*) echo "centos6" ;;
            'Red Hat Enterprise Linux Server release 5'*) echo "rhel5" ;;
            *) "rhel" ;;
        esac
    else
        echo "unknown"
    fi
}

detect_solaris_release() {
    local version=`uname -v`
    echo "solaris$version"
}

detect_os() {
    case `uname` in
        Linux) detect_linux_distro ;;
        SunOS) detect_solaris_release ;;
        *) echo "unknown" ;;
    esac
}
