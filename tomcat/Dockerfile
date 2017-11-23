FROM tomcat:7.0.72-jre7
RUN apt-get update && apt-get install -y gettext bash
COPY ./service-print-main.war /usr/local/tomcat/webapps/service-print-main.war
COPY checker /usr/local/tomcat/webapps/ROOT/checker
