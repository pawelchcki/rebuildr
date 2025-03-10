#! /usr/bin/env nix
#! nix shell path:../ --command rebuildr parse-py
from rebuildr.descriptor import Descriptor, EnvInput, FileInput, Inputs

image = Descriptor(
    inputs=Inputs(
        env=[
            EnvInput(key="EXAMPLE_ENV"),
        ],
        files=[
            FileInput(path="test.txt"),
        ],
        dockerfile="simple.Dockerfile",
    ),
)
