FROM alpine:3.6
MAINTAINER procrastinatio
COPY . /print3
WORKDIR /print3
RUN apk add --update py-pip python-dev make bash gcc git ncurses libc-dev gettext
RUN make cleanall && \
       pip install -r requirements.txt \
       && pip install -r dev-requirements.txt \
       && pip install .

ENTRYPOINT ["/print3/docker-entrypoint.sh"]

CMD ["python", "print3/wsgi.py]

