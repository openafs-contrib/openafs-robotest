#!/usr/bin/env python

import os
import sys
import syslog
import SimpleHTTPServer
import SocketServer

class MyHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        syslog.syslog("%s - - [%s] %s\n" % (self.client_address[0],
                  self.log_date_time_string(), format % args))

def daemonize():
    pid = os.fork()
    if pid < 0:
        sys.stderr.write("Failed to fork!\n")
    elif pid != 0:
        # parent process
        print "Started process id %d." % (pid)
        sys.exit(0)
    else:
        # child process
        return

def main(args):
    try:
        import settings
    except ImportError:
        print "Please do `./run.py setup' first."
        sys.exit(1)
    if not os.path.exists(settings.RF_OUTPUT):
        os.makedirs(settings.RF_OUTPUT)
    os.chdir(settings.RF_OUTPUT)
    httpd = SocketServer.TCPServer(("", settings.WEBSERVER_PORT), MyHTTPRequestHandler)
    syslog.openlog(ident='webserver', logoption=syslog.LOG_PID, facility=syslog.LOG_DAEMON)
    syslog.syslog("Starting openafs-robotest webserver on port %d ..." % settings.WEBSERVER_PORT)
    daemonize()
    httpd.serve_forever()

if __name__ == "__main__":
    main(sys.argv[1:])
