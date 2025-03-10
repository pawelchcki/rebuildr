#! /usr/bin/env nix
#! nix shell path:../ --command rebuildr parse-py
from rebuildr.descriptor import Descriptor, EnvInput, FileInput, GlobInput, Inputs

image = Descriptor(
    inputs=Inputs(
        env=[
            EnvInput(key="EXAMPLE_ENV"),
        ],
        files=[
            GlobInput(pattern="*.txt"),
        ],
        dockerfile="simple.Dockerfile",
    ),
)
