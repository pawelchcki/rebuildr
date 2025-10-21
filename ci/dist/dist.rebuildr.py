#! /usr/bin/env nix
#! nix shell path:../.. --command rebuildr load-py

import os
from rebuildr.descriptor import Descriptor, FileInput, GlobInput, ImageTarget, Inputs

# Get tag from environment variable, default to "latest"
tag = os.environ.get("REBUILDR_DIST_TAG", "latest")
repository = os.environ.get(
    "REBUILDR_DIST_REPOSITORY", "ghcr.io/pawelchcki/rebuildr/dist"
).lower()
# lowercase the repository name to satisfy ghcr restrictions

image = Descriptor(
    targets=[
        ImageTarget(
            dockerfile="dist.Dockerfile",
            repository=repository,
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
