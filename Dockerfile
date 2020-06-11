FROM alpine:3.9
MAINTAINER procrastinatio
RUN apk add --update py-pip python3-dev make bash g++ git ncurses libc-dev gettext cython poppler-utils
WORKDIR /print3
COPY requirements.txt /print3/requirements.txt
COPY dev-requirements.txt /print3/dev-requirements.txt
COPY Makefile /print3/Makefile
RUN make cleanall && pip3 install -r requirements.txt \
       && pip3 install -r dev-requirements.txt 
COPY . /print3
RUN pip3 install .
