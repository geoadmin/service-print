FROM        tomcat:7.0.72-jre7

MAINTAINER  Marc Monnerat (marc.monenrat@swisstopo.ch)

COPY        ./software/ /usr/local/tomcat/webapps/
