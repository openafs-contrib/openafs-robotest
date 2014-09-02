#!/usr/bin/env python

import os
import SimpleHTTPServer
import SocketServer

PORT = 8000
RUN_OUTPUT_DIR="output"

# parse settings to get custom RUN_OUTPUT_DIR
f=file("settings", "r")
while 1 :
    line = f.readline()
    if not line : break
    line = line.strip()
    if line.startswith("RUN_OUTPUT_DIR") :
         RUN_OUTPUT_DIR = line.split("#")[0].split("=")[1].replace("\"","")
         break
f.close()

Handler = SimpleHTTPServer.SimpleHTTPRequestHandler

os.chdir(RUN_OUTPUT_DIR)

httpd = SocketServer.TCPServer(("", PORT), Handler)

print "serving at port", PORT
httpd.serve_forever()
