FROM alpine:3.6
MAINTAINER loicgasser
COPY . /print3
WORKDIR /print3
RUN apk add --update py-pip python-dev make bash
RUN make cleanall \
    && pip install -r requirements.txt \
        && pip install -r dev-requirements.txt \
            && pip install .
