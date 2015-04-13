# Copyright (c) 2014, Sine Nomine Associates
# See LICENSE

import os as _os

OS_NAME = _os.uname()[0]
OS_NODE = _os.uname()[1]
OS_RELEASE = _os.uname()[2]
OS_VERSION = _os.uname()[3]
OS_MACHINE = _os.uname()[4]

HOSTNAME = OS_NODE  # alias

