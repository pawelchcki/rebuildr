from rebuildr.descriptor import (
    ArgsInput,
    Descriptor,
    EnvInput,
    GlobInput,
    ImageTarget,
    Inputs,
)

image = Descriptor(
    targets=[
        ImageTarget(
            dockerfile="simple.Dockerfile",
            repository="registry.ddbuild.io/ci/rebuildr/simple",
        ),
    ],
    inputs=Inputs(
        builders=[
            EnvInput(key="_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"),
            ArgsInput(key="arg"),
        ],
        files=[
            GlobInput(pattern="*.txt"),
        ],
    ),
)
