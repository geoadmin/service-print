#!/bin/bash
set -e

#envsubst < nginx.conf.in > /usr/local/openresty/nginx/conf/nginx.conf
#envsubst < default.conf.in > /etc/nginx/conf.d/default.conf

#cp openresty.conf /usr/local/openresty/nginx/conf/nginx.conf
#envsubst "`printf '${%s} ' $(bash -c "compgen -A variable")`"  < default.conf.in > /etc/nginx/conf.d/default.conf
envsubst "`printf '${%s} ' $(bash -c "compgen -A variable")`"  < nginx.conf.in > /usr/local/openresty/nginx/conf/nginx.conf
#cp default.conf.in  /etc/nginx/conf.d/default.conf

# Always put this damn shit
exec "$@"
