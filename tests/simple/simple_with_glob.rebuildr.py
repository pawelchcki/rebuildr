#! /usr/bin/env nix
#! nix shell path:../ --command rebuildr parse-py
from rebuildr.descriptor import (
    Descriptor,
    Dockerfile,
    EnvInput,
    FileInput,
    GlobInput,
    Inputs,
)

image = Descriptor(
    inputs=Inputs(
        builders=[
            EnvInput(key="_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"),
            Dockerfile("simple.Dockerfile"),
        ],
        files=[
            GlobInput(pattern="*.txt"),
        ],
    ),
)
