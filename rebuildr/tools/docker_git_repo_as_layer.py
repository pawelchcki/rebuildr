def dockerfile_parametrized(owner: str, repo: str, commit: str) -> str:
    return f"""
FROM alpine/git@sha256:3ed9c9f02659076c2c1fe10de48a8851bc640b7133b3620a7be7a148e4a92715 as fetcher

WORKDIR /repo
RUN set -eux; \
    git clone https://github.com/{owner}/{repo}.git . -b {commit} --single-branch;

FROM scratch
COPY --from=fetcher /repo /
"""
