#! /usr/bin/env nix
#! nix shell path:../../../../ --command rebuildr load-py
from rebuildr.descriptor import (
    Descriptor,
    GitHubCommitInput,
    Inputs,
    ImageTarget,
)

image = Descriptor(
    inputs=Inputs(
        external=[
            GitHubCommitInput(
                owner="aliml92",
                repo="realworld-gin-sqlc",
                commit="f01271b55086265c3e07191fff469f4b902ecf96",
                target_path="/src",
            ),
        ],
    ),
    targets=[
        ImageTarget(
            repository="ghcr.io/aliml92/realworld-gin-sqlc",
            tag="v0",
            dockerfile="Dockerfile",
            platform="linux/amd64",
        ),
    ],
)
