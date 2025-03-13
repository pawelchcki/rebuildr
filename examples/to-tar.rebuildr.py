#! /usr/bin/env nix
#! nix shell path:../ --command rebuildr build-tar
from rebuildr.descriptor import (
    Descriptor,
    Dockerfile,
    EnvInput,
    FileInput,
    Inputs,
    TagTarget,
)

image = Descriptor(
    Inputs(
        files=[
            "test.txt",
        ],
    ),
)
