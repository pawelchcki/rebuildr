FROM python:3.12-alpine

WORKDIR /app
# Create an entrypoint script
RUN printf '#!/bin/sh\nif [ "$1" = "sh" ]; then\n  exec sh\nelse\n  python -m rebuildr.cli "$@"\nfi' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

COPY . .

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

