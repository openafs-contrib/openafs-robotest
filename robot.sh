#!/bin/sh
robot -P resources -V config/settings.yaml -V config/paths.yaml -A config/args.txt tests
