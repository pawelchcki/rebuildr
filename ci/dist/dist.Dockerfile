FROM bash:latest
RUN apk add python3

COPY / /
WORKDIR /target
