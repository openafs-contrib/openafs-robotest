#
# Common shell functions for linux-based systems.
#

#------------------------------------------------------------------------------
# Add a user to create the AFS cell and run the tests.
#
create_tester() {
    local username=${1:-"afsrobot"}
    local group=${2:-"testers"}
    getent passwd $username >/dev/null || useradd -m $username
    getent group $group >/dev/null || groupadd $group
    usermod -G $group $username || true
    cat <<EOF >/etc/sudoers.d/afsrobot
# Allow testers to install and remove OpenAFS.
%${group} ALL=(root) NOPASSWD: /bin/afsutil,/usr/bin/afsutil,/usr/local/bin/afsutil
EOF
    chmod 0440 /etc/sudoers.d/afsrobot
}

#------------------------------------------------------------------------------
# Detect the inet address of the given device. If no device name is given,
# try to find the inet address of the first link which is up.
#
detect_ip() {
    local device=$1
    if [ -z $device ]; then
        ip addr | grep -A2 'state UP' | tail -1 | awk '{print $2}' | cut -f1 -d'/'
    elif ip link show $device >/dev/null; then
        ip addr show $device | tail -3 | head -1 | awk '{print $2}' | cut -f1 -d'/'
    else
        return 1
    fi
}

#------------------------------------------------------------------------------
# Replace loopback entries in /etc/hosts with the given ip address.
#
fixup_etc_hosts() {
    local hosts='/etc/hosts'
    local ip=`detect_ip $1` || { echo "Unable to lookup ip address." >&2; return 1; }
    local hostname=`hostname`

    case "$ip" in
    "127."*)  echo "fixup_etc_hosts requires a non-loopback address." >&2; return 1;;
    "") echo "usage: fixup_etc_hosts <ip>" >&2; return 1;;
    *) ;;
    esac

    test -f $hosts || { echo "Cannot find $hosts!" >&2; return 1; }
    cp $hosts $hosts.old || { echo "Failed to copy $hosts to $hosts.old" >&2; return 1; }

    awk -f- -v "ip=$ip" -v "hostname=$hostname" -- $hosts.old >$hosts.new <<'EOF'
        BEGIN { seen=0 }
        /^[0-9]/ && !/^127\./ && ($2==hostname || $3==hostname) { seen=1 }
        /^127\./ && ($2==hostname || $3==hostname) { print "#",$0; next }
        { print }
        END { if (!seen) { printf("%s\t%s\n", ip, hostname) }}
EOF
    if [ $? -ne 0 ]; then
        echo "Failed to update $hosts" >&2
        return 1
    fi
    cp $hosts.new $hosts || { echo "Failed to copy $hosts.new to $hosts" >&2; return 1; }
}
