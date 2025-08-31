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
