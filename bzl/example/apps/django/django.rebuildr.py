from rebuildr.descriptor import (
    Descriptor,
    FileInput,
    GitHubCommitInput,
    Inputs,
    ImageTarget,
)

image = Descriptor(
    inputs=Inputs(
        files=[
            FileInput(
                path="Dockerfile",
                target_path="Dockerfile.1",
            ),
        ],
        external=[
            GitHubCommitInput(
                owner="Sean-Miningah",
                repo="realWorld-DjangoRestFramework",
                commit="master",  # Using master branch, can be pinned to specific commit
                target_path="src",
            ),
        ],
    ),
    targets=[
        ImageTarget(
            repository="registry.ddbuild.io/build/realworld/django-rest-framework",
            tag="v0",
            dockerfile="Dockerfile",
            platform="linux/amd64",
        ),
    ],
)
