from rebuildr.descriptor import (
    Descriptor,
    GitHubCommitInput,
    Inputs,
    ImageTarget,
)

image = Descriptor(
    inputs=Inputs(
        external=[
            GitHubCommitInput(
                owner="gothinkster",
                repo="aspnetcore-realworld-example-app",
                commit="b04d12347fb0137f2cf96ea1be8ee689ea658374",
                target_path="src",
            ),
        ],
    ),
    targets=[
        ImageTarget(
            repository="registry.ddbuild.io/build/gothinkster/aspnetcore-realworld-example-app",
            tag="v0",
            dockerfile="Dockerfile",
            platform="linux/amd64",
        ),
    ],
)
