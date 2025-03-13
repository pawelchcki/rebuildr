#! /usr/bin/env nix
#! nix shell path:../ --command rebuildr parse-py
from rebuildr.descriptor import Descriptor, Dockerfile, EnvInput, FileInput, GlobInput, Inputs

image = Descriptor(
    inputs=Inputs(
        builders=[
            EnvInput(key="EXAMPLE_ENV"),
            Dockerfile("simple.Dockerfile"),
        ],
        files=[
            GlobInput(pattern="*.txt"),
        ],
    ),
)
