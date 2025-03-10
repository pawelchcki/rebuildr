#! /usr/bin/env nix
#! nix shell path:../ --command rebuildr load-py

from rebuildr.descriptor import Descriptor, GlobInput, ImageTarget, Inputs

image = Descriptor(
    targets=[
        ImageTarget(
            dockerfile="small.Dockerfile",
            repository="registry.ddbuild.io/ci/rebuildr/small",
            tag="latest",
        )
    ],
    inputs=Inputs(
        files=[
            GlobInput(
                pattern="rebuildr/**/*.py",
                root_dir="..",
            )
        ]
    ),
)
