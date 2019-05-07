FROM alpine:3.9
MAINTAINER procrastinatio
COPY . /print3
WORKDIR /print3
RUN apk add --update py-pip python3-dev make bash g++ git ncurses libc-dev gettext cython poppler-utils
RUN make cleanall && pip3 install -r requirements.txt \
       && pip3 install -r dev-requirements.txt \
       && pip3 install .
