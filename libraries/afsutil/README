Helpers to install and setup OpenAFS.

# Python Modules

Except for the afsutil command line tool, the afsutil modules have no
dependencies on third party modules. The installation script depends on
setuptools.

* setuptools  - for installation
* argparse    - for the afsutil command line tool
* argcomplete - afsutil tab completion (optional)

Install pip and setuptools if they are not already on your system.  Python
2.7.9 and later (on the python2 series), and Python 3.4 and later include pip
by default, so you may have pip already.

To install pip and setuptools on deb based systems:

    $ sudo apt-get install python-pip

To install pip and setuptools on rpm based systems:

    $ sudo yum install python-pip

To install argparse (if not already present):

    $ sudo pip install argparse

To install argcomplete (optional):

    $ sudo pip install argcomplete


# Installation

To install the afsutil package:

    $ sudo ./install.sh


# Command-line Completion [optional]

Command-line tab completion for afsutil in bash and zsh is provided by the
argcomplete module when the argcomplete module is available.

To install the command-line completion support:

    $ sudo pip install argcomplete
    $ sudo activate-global-python-argcomplete

Then refresh your bash environment by starting a new shell or sourcing
/etc/profile in the current shell:

    $ . /etc/profile

The following can be to be put in ~/.bashrc instead of activating global
completion:

    eval "$(register-python-argcomplete afsutil)"


