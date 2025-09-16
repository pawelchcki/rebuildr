from rebuildr.descriptor import (
    ArgsInput,
    Descriptor,
    EnvInput,
    GlobInput,
    Inputs,
    ImageTarget,
)

image = Descriptor(
    inputs=Inputs(
        files=[
            GlobInput(pattern="**/*"),
        ],
        builders=[
            ArgsInput(key="TEST_ARG"),
            EnvInput(key="TEST_ENV"),
        ],
    ),
    targets=[
        ImageTarget(
            repository="registry.ddbuild.io/ci/rebuildr/test-image",
            tag="latest",
            dockerfile="Dockerfile",
        ),
    ],
)
