#!/usr/bin/env python

import os
import sys
import SimpleHTTPServer
import SocketServer

def main(args):
    try:
        import settings
    except ImportError:
        print "Please do `./run setup' first."
        sys.exit(1)
    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    if not os.path.exists(settings.RF_OUTPUT):
        os.makedirs(settings.RF_OUTPUT)
    os.chdir(settings.RF_OUTPUT)
    httpd = SocketServer.TCPServer(("", settings.WEBSERVER_PORT), Handler)
    print "Serving at port %d, use <Ctrl-C> to stop." % settings.WEBSERVER_PORT
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main(sys.argv[1:])
