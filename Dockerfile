FROM        tomcat:7.0.72-jre7

MAINTAINER  Marc Monnerat (marc.monnerat@swisstopo.ch)

COPY        ./software/ /usr/local/tomcat/webapps/

EXPOSE 8080
