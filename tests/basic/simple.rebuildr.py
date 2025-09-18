from rebuildr.descriptor import Descriptor, EnvInput, FileInput, ImageTarget, Inputs

image = Descriptor(
    targets=[
        ImageTarget(
            dockerfile="simple.Dockerfile",
            repository="registry.ddbuild.io/ci/rebuildr/simple",
        ),
    ],
    inputs=Inputs(
        files=[
            FileInput("test.txt"),
            FileInput("test.txt", target_path="test_renamed.txt"),
        ],
        builders=[
            EnvInput("_TEST_VALUE_IS_NEVER_SET_ON_TEST_SYSTEM"),
        ],
    ),
)
