FROM tomcat:7.0.82-jre7
RUN apt-get update && apt-get install -y gettext bash tzdata
ENV TZ=Europe/Zurich
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY ./service-print-main.war /usr/local/tomcat/webapps/service-print-main.war
COPY checker /usr/local/tomcat/webapps/ROOT/checker
COPY server.xml /usr/local/tomcat/config/server.xml
COPY *.ttf /usr/share/fonts/truetype/
