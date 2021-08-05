FROM tomcat:7-jre7

# setup base
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -y gettext bash tzdata apt-utils
ENV TZ=Europe/Zurich
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get install --reinstall -y locales
# uncomment chosen locale to enable it's generation
RUN sed -i 's/# de_CH.UTF-8 UTF-8/de_CH.UTF-8 UTF-8/' /etc/locale.gen
# generate chosen locale
RUN locale-gen de_CH.UTF-8
# set system-wide locale settings
ENV LANG de_CH.UTF-8
ENV LANGUAGE de_CH
ENV LC_ALL de_CH.UTF-8
# verify modified configuration
RUN dpkg-reconfigure --frontend noninteractive locales
COPY ./service-print-main.war /usr/local/tomcat/webapps/service-print-main.war
COPY checker /usr/local/tomcat/webapps/ROOT/checker
COPY server.xml /usr/local/tomcat/config/server.xml
COPY *.ttf /usr/share/fonts/truetype/
