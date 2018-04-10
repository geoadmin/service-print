FROM nginx:1.13.3
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get remove -y nginx && apt-get install -y gettext bash nginx-full
RUN rm /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY . /.
COPY log_format.conf /etc/nginx/log_format.conf
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
