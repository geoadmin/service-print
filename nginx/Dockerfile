FROM openresty/openresty:1.13.6.2-0-stretch-fat
RUN apt-get update && apt-get install -y gettext bash
COPY . /.
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
