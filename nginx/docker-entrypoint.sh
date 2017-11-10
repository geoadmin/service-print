#!/bin/bash
set -e

envsubst < nginx.conf.in > /etc/nginx/nginx.conf

# Always put this damn shit
exec "$@"
