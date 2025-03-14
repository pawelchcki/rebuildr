ARG PYTHON_VERSION=3.12

FROM python:3.12-alpine AS small

WORKDIR /app
# Create an entrypoint script
RUN printf '#!/bin/sh\nif [ "$1" = "sh" ]; then\n  exec sh\nelse\n  python -m rebuildr.cli "$@"\nfi' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

COPY . .

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]


FROM alpine as builder
ARG PYTHON_VERSION
ARG TARGETARCH


RUN set -xe; apk add --no-cache python3~=${PYTHON_VERSION}
WORKDIR /usr/lib/python${PYTHON_VERSION}
RUN python -m compileall -o 2 .
RUN find . -name "*.cpython-*.opt-2.pyc" | awk '{print $1, $1}' | sed 's/__pycache__\///2' | sed 's/.cpython-[0-9]\{2,\}.opt-2//2' | xargs -n 2 mv
# RUN find . -mindepth 1 | grep -v -E '^\./(encodings|importlib|warnings|types|logging|dataclasses|s)([/.].*)?$' | xargs rm -rf
RUN find . -name "*.py" -delete
RUN find . -name "__pycache__" -exec rm -r {} +

WORKDIR /export
RUN mkdir -p ./usr/bin 
RUN cp /usr/bin/python3 ./usr/bin/python3
RUN mkdir -p ./lib
RUN set -xe; \
    if [ "$TARGETARCH" = "amd64" ]; then \
      ARCH="x86_64"; \
    elif [ "$TARGETARCH" = "arm64" ]; then \
      ARCH="aarch64"; \
    elif [ "$TARGETARCH" = "arm" ]; then \
      ARCH="armv7"; \
    elif [ "$TARGETARCH" = "386" ]; then \
      ARCH="x86"; \
    else \
      ARCH="$TARGETARCH"; \
    fi && \
    echo "Mapping $TARGETARCH to $ARCH for Alpine Linux"; \
    cp /lib/ld-musl-${ARCH}.so.1 ./lib/ld-musl-${ARCH}.so.1
RUN mkdir -p ./usr/lib/python${PYTHON_VERSION}
# RUN cp /usr/lib/libpython${PYTHON_VERSION}.so.1.0 ./usr/lib/libpython${PYTHON_VERSION}.so.1.0
# RUN cp -r /usr/lib/python${PYTHON_VERSION} ./usr/lib/python${PYTHON_VERSION}

FROM scratch as teeny-tiny
ARG PYTHON_VERSION

COPY --from=builder /export/ /
# COPY --from=builder /usr/bin/python3 /
# COPY --from=builder /lib/ld-musl-${TARGETPLATFORM}.so.1 /lib/ld-musl-${TARGETPLATFORM}.so.1
COPY --from=builder /usr/lib/libpython${PYTHON_VERSION}.so.1.0 /usr/lib/libpython${PYTHON_VERSION}.so.1.0
COPY --from=builder /usr/lib/python${PYTHON_VERSION}/ /usr/lib/python${PYTHON_VERSION}/

WORKDIR /app

COPY . .

# Set the entrypoint
ENTRYPOINT ["/usr/bin/python3", "-m", "rebuildr.cli"]