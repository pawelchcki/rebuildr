#! /usr/bin/env nix
#! nix shell path:../ --command rebuildr parse-py
from rebuildr.descriptor import (
    Descriptor,
    Dockerfile,
    EnvInput,
    FileInput,
    Inputs,
    TagTarget,
)

image = Descriptor(
    targets=[
        TagTarget(
            repository="firstimage",
            tag="latest",
        ),
    ],
    inputs=Inputs(
        files=[
            FileInput(path="test.txt"),
        ],
        # any dependencies, files or paths that are required for builing but do not go into final artifact
        builders=[
            EnvInput(key="DOCKER_BUILDKIT"),
            Dockerfile("first.Dockerfile"),
        ],
    ),
)
