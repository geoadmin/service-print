FROM nginx:1.13.3
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -y gettext bash
RUN rm /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY . /.
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
