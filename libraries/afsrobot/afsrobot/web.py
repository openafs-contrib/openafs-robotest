# Copyright (c) 2015-2016 Sine Nomine Associates
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import atexit
import os
import signal
import SimpleHTTPServer
import SocketServer
import sys
import time


class SilentRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """Handle requests without printing messages."""
    def log_message(self, format, *args):
        pass

class TinyWebServer(object):
    """Minimal web server to display test reports and logs.

    This optional helper is provided as a simple way to view the test
    reports and logs.  This only serves static content.
    """
    def __init__(self, config):
        run = '/tmp'  # Should be /var/run/<dir>, with proper perms.
        pidfile = "afsrobot-%d.pid" % (os.getuid())
        self.pidfile = os.path.join(run, pidfile)
        self.port = config.getint('web', 'port')
        self.docroot = config.get('paths', 'html')
        self.foreground = config.getboolean('web', 'foreground')

    def _exit(self):
        """Clean up our pid file."""
        try:
            os.remove(self.pidfile)
        except:
            pass

    def _getpid(self):
        """Get the child process pid from the pid file."""
        pid = 0
        try:
            with open(self.pidfile) as f:
                pid = int(f.readline().strip())
        except:
            pass
        return pid

    def _daemonize(self):
        """Simplified daemonize to run the server in the background."""
        pid = os.fork()
        if pid < 0:
            raise AssertionError("Failed to fork!\n")
        if pid != 0:
            sys.exit(0) # Parent process
        # Child process
        os.setsid() # detach
        atexit.register(self._exit)
        with open(self.pidfile, "w") as f:
            f.write("%d\n" % os.getpid())

    def start(self):
        """Start the miminal web server."""
        pid = self._getpid()
        if pid:
            sys.stderr.write("Already running (pid %d).\n" % (pid))
            return
        if not os.path.isdir(self.docroot):
            os.makedirs(self.docroot)
        os.chdir(self.docroot)
        sys.stdout.write("Listening at http://%s:%d\n" % (os.uname()[1], self.port))
        if not self.foreground:
            self._daemonize()
        address = ('', self.port)
        Handler = SilentRequestHandler
        Handler.extensions_map['.log'] = 'text/plain'
        server = SocketServer.TCPServer(address, Handler)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        sys.exit(0)

    def stop(self):
        """Stop the miminal web server."""
        if self.foreground:
            sys.stderr.write("Skipping stop; foreground mode.\n")
            return
        pid = self._getpid()
        if pid == 0:
            sys.stdout.write("Not running.\n")
        else:
            sys.stdout.write("Stopping process %d... " % (pid))
            sys.stdout.flush()
            os.kill(pid, signal.SIGINT)
            for _ in xrange(0,10):
                time.sleep(1)
                if self._getpid() == 0:
                    sys.stdout.write("ok.\n")
                    return
            sys.stdout.write("failed.\n")

    def status(self):
        """Get the status of the miminal web server."""
        if self.foreground:
            sys.stderr.write("Skipping status; foreground mode.\n")
            return ""
        pid = self._getpid()
        if pid:
            status = "Process %d listening at http://%s:%d." % (pid, os.uname()[1], self.port)
        else:
            status = "Not running."
        return status

