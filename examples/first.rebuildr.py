#! /usr/bin/env nix
#! nix shell path:../ --command rebuildr parse-py
from rebuildr.descriptor import Descriptor, EnvInput, FileInput, Inputs, TagTarget

image = Descriptor(
    targets=[
        TagTarget(
            repository="firstimage",
            tag="latest",
        ),
    ],
    inputs=Inputs(
        env=[
            EnvInput(key="DOCKER_QUIET"),
        ],
        files=[
            FileInput(path="test.txt"),
        ],
        dockerfile="first.Dockerfile",
    ),
)
