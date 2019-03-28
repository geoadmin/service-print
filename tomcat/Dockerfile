FROM swisstopo/tomcat7-base

ENV DEBIAN_FRONTEND noninteractive
ENV TZ=Europe/Zurich
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY ./service-print-main.war /usr/local/tomcat/webapps/service-print-main.war
COPY checker /usr/local/tomcat/webapps/ROOT/checker
COPY server.xml /usr/local/tomcat/config/server.xml
COPY *.ttf /usr/share/fonts/truetype/
