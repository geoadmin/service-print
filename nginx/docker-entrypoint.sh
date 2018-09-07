#!/bin/bash
set -e

# Only replace variable that exists, nginx uses $ that must not be replaced
envsubst "`printf '${%s} ' $(bash -c "compgen -A variable")`"  < nginx.conf.in > /usr/local/openresty/nginx/conf/nginx.conf

# Always put this damn shit
exec "$@"
