FROM debian:buster-slim
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -y gettext bash tzdata apt-utils
MAINTAINER webgis@swisstopo.ch


RUN groupadd -r geoadmin && useradd -r -s /bin/false -g geoadmin geoadmin

RUN apt-get update && apt-get install apt-utils \
  ; DEBIAN_FRONTEND=noninteractive apt-get install -y --upgrade ca-certificates \
 ; DEBIAN_FRONTEND=noninteractive apt-get install -y -o Dpkg::Options::="--force-confold" \
    bash \
    curl \
    g++ \
    make \
    proj-bin \
    python3.7-minimal \
    python3-dev \
    python3-pip \
    zlib1g-dev \
    ncurses-bin \
    libc-dev \
    gettext \
    cython \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /print3
COPY requirements.txt /print3/requirements.txt
COPY dev-requirements.txt /print3/dev-requirements.txt
COPY Makefile /print3/Makefile
RUN make cleanall && pip3 install -r requirements.txt \
       && pip3 install -r dev-requirements.txt 
COPY . /print3
RUN pip3 install .


RUN chown -R geoadmin:geoadmin /print3
USER geoadmin

ENTRYPOINT ["python3", "print3/wsgi.py"]
