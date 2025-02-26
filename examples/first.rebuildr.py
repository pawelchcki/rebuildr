#! /usr/bin/env nix
#! nix shell path:../ --command rebuildr parse-py
from rebuildr.descriptor import Descriptor, EnvInput, FileInput, Inputs

image = Descriptor(
    inputs=Inputs(
        env=[
            EnvInput(key="DOCKER_QUIET"),
        ],
        files=[
            "test.txt",
        ],
        dockerfile="first.Dockerfile",
    ),
)
