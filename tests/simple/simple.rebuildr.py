#! /usr/bin/env nix
#! nix shell path:../ --command rebuildr parse-py
from rebuildr.descriptor import Descriptor, Dockerfile, EnvInput, FileInput, Inputs

image = Descriptor(
    Inputs(
        files=[
            FileInput("test.txt"),
        ],
        builders=[
            EnvInput("_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"),
            Dockerfile("simple.Dockerfile"),
        ],
    ),
)
