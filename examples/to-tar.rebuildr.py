#! /usr/bin/env nix
#! nix shell path:../ --command rebuildr build-tar
from rebuildr.descriptor import (
    Descriptor,
    Inputs,
)

image = Descriptor(
    Inputs(
        files=[
            "test.txt",
        ],
    ),
)
