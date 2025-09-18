#! /usr/bin/env nix
#! nix shell path:../.. --command rebuildr load-py

from rebuildr.descriptor import Descriptor, FileInput, GlobInput, ImageTarget, Inputs

image = Descriptor(
    targets=[
        ImageTarget(
            dockerfile="dist.Dockerfile",
            repository="ghcr.io/pawelchcki/rebuildr/dist",
            tag="latest",
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
