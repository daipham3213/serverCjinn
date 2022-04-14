# pull official base image
FROM python:3.9.6-alpine

# set work directory
WORKDIR /usr/src/app

ENV DEBIAN_FRONTEND noninteractive
ENV TZ=UTC

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install libaries
RUN apk add --no-cache postgresql-libs && \
    apk add --no-cache alpine-sdk autoconf automake libtool && \
    apk add --no-cache --virtual .build-deps g++ musl-dev postgresql-dev libffi-dev

# install dependencies
RUN pip3 install --upgrade pip
RUN python3 -m pip install --upgrade setuptools
COPY ./requirements.txt .
RUN python3 -m pip install -r requirements.txt --no-cache-dir && \
 apk --purge del .build-deps

# copy project
COPY . .