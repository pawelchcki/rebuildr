FROM python:3.12-alpine AS small

WORKDIR /app

# Create an entrypoint script
RUN set -xe; \
    printf '#!/bin/sh\nPYTHONPATH=/app python -m rebuildr.cli "$@"\n' > /usr/bin/rebuildr; \
    chmod +x /usr/bin/rebuildr

COPY . .

ENTRYPOINT [ "/bin/sh" ]