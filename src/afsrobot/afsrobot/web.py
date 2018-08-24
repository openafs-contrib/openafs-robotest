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

from __future__ import print_function
import os
import SimpleHTTPServer
import SocketServer

def run(config, **kwargs):
    """Minimal web server to display test reports and logs.

    This minimal http server is provided as a simple way to view the test
    reports and logs.
    """
    port = config.getint('web', 'port')
    docroot = config.get('web', 'docroot')
    if not os.path.isdir(docroot):
        print("Creating directory '%s'." % (docroot,))
        os.makedirs(docroot)
    print("Changing to docroot directory '%s'." % (docroot,))
    os.chdir(docroot)

    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    Handler.extensions_map['.log'] = 'text/plain'

    SocketServer.TCPServer.allow_reuse_address = True
    httpd = SocketServer.TCPServer(('', port), Handler)
    try:
        print("Listening on port %d." % (port,))
        print("(Press <Control>-c to stop.)")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        httpd.server_close()
