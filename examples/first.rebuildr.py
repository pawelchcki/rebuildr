#! /usr/bin/env nix
#! nix shell path:../ --command rebuildr parse-py
from rebuildr.descriptor import (
    Descriptor,
    EnvInput,
    FileInput,
    Inputs,
    ImageTarget,
)

image = Descriptor(
    targets=[
        ImageTarget(
            repository="firstimage",
            tag="latest",
            dockerfile="first.Dockerfile",
        ),
    ],
    inputs=Inputs(
        files=[
            FileInput(path="test.txt"),
        ],
        # any dependencies, files or paths that are required for builing but do not go into final artifact
        builders=[
            EnvInput(key="DOCKER_BUILDKIT"),
        ],
    ),
)
