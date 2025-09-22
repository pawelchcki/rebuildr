#! /usr/bin/env nix
#! nix shell path:../.. --command rebuildr load-py

import os
from rebuildr.descriptor import Descriptor, FileInput, GlobInput, ImageTarget, Inputs

# Get tag from environment variable, default to "latest"
tag = os.environ.get("REBUILDR_TAG", "latest")

image = Descriptor(
    targets=[
        ImageTarget(
            dockerfile="dist.Dockerfile",
            repository="ghcr.io/pawelchcki/rebuildr/dist",
            tag=tag,
        )
    ],
    inputs=Inputs(
        files=[
            GlobInput(
                pattern="rebuildr/**/*.py",
                root_dir="../..",
                target_path="target/dist/rebuildr_impl/",
            ),
            FileInput(
                path="rebuildr_dist_wrapper.sh",
                target_path="target/dist/rebuildr",
            ),
            FileInput(
                path="tar.dist.sh",
                target_path="target/tool/tar",
            ),
        ]
    ),
)
