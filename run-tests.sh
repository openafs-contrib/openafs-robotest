#!/bin/sh

# Run options
RUN_OUTPUT_DIR="output"
RUN_TAGS="precheck,install,smoke"

# Test variables
_varnames=`cat <<__EOF__
AFS_CELL
AFS_HOST
AFS_SUPERUSER
AFS_TESTUSER
ENV_FS
ENV_DIST
ENV_KEY
IBM_DEST
KRB_AFS_KEYTAB
KRB_REALM
KRB_RXKAD_KEYTAB
KRB_USER_KEYTAB
RPM_AFSRELEASE
RPM_AFSVERSION
RPM_PACKAGE_DIR
__EOF__`

# default values
AFS_CELL="robotest"
AFS_HOST=`hostname -f`
AFS_SUPERUSER="robotest.admin"
AFS_TESTUSER="robotest"
ENV_FS="fs"
ENV_DIST="redhat"
ENV_KEY="k5"
IBM_DEST=""
KRB_AFS_KEYTAB="keytabs/afs.keytab"
KRB_REALM="LOCALREALM"
KRB_RXKAD_KEYTAB="keytabs/rxkad.keytab"
KRB_USER_KEYTAB="keytabs/robotest.keytab"
RPM_AFSRELEASE="1"
RPM_AFSVERSION=""
RPM_PACKAGE_DIR="$HOME/rpmbuild/RPMS/x86_64"

usage() {
    cat <<__EOF__
usage: run-tests.sh [options]
options are:
    -h|--help
    --runtest-output-dir <value>
    --runtest-tags <value>
__EOF__
    for _v in $_varnames
    do
        echo $_v | tr A-Z a-z | sed 's/_/-/g; s/^/    --/; s/$/ <value>/'
    done
}

check_error() {
    if [ $1 != 0 ]; then
        echo testcase $2 failed. Terminating.
        exit $1
    fi
}

# Custom settings are overwiden by command line options.
if [ -f ./settings ]; then
    . ./settings
fi

while [ $# -gt 0 ]
do
    _opt=$1
    shift
    case $_opt in
        -h|--help)
            usage
            exit 0
            ;;
        --run-output-dir)
            RUN_OUTPUT_DIR=$1
            shift
            ;;
        --run-tags)
            RUN_TAGS=$1
            shift
            ;;
        *)
            _varname=`echo $_opt | sed 's/^--//; s/-/_/g' | tr a-z A-Z`
            if echo $_varnames | grep -q -w $_varname; then
                :
            else
                echo "error: unknown option: $_opt" 1>&2
                exit 1
            fi
            if [ "x$1" = "x" ]; then
                echo "error: missing value for $_opt" 1>&2
                exit 1
            fi
            eval $_varname=$1
            shift
            ;;
    esac
done

_vars=""
_tags=""
for _varname in $_varnames
do
    eval _varval=\$$_varname
    _vars="$_vars -v $_varname:$_varval"
    if echo $_varname | grep -q '^ENV_'; then
        _tags="$_tags -i env-$_varval"
    fi
done


_tags="precheck install($ENV_DIST)"

for _tag_file in `ls tests/smoke`
do
    for _tag in `echo $RUN_TAGS | sed 's/[,:]/ /g'`
    do
        if [ `grep DefaultTags tests/smoke/$_tag_file |awk '{print $NF}'`  != $_tag ]; then
            continue
        fi
        if [ "x$_tag" != "x" ]; then 
            if [ `echo -- $_tags | grep -c -w $_tag` = 0 ] ;then 
               _tags="$_tags $_tag"
            fi
        fi
    done
done

for _tag in $_tags
do
    RUNTEST="pybot --exitonfailure --outputdir $RUN_OUTPUT_DIR -i $_tag $_vars tests"
    echo "running: $RUNTEST"
    $RUNTEST
    check_error $? $_tag
done

