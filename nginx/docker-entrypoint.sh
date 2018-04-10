#!/bin/bash
set -e

envsubst "$(printf '${%s} ' $(/bin/bash -c "compgen -A variable"))" < nginx.conf.in > /etc/nginx/nginx.conf

# Always put this damn shit
exec "$@"
