#!/bin/bash
set -e

envsubst < print3/wsgi.py.in >  print3/wsgi.py

envsubst < production.ini.in > production.ini

# Always put this damn shit
exec "$@"
