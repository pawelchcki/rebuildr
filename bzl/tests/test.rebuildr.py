from rebuildr.descriptor import Descriptor, GlobInput, Inputs, FileInput, ImageTarget

image = Descriptor(
    inputs=Inputs(
        files=[
            GlobInput(pattern="**/*"),
        ],
        builders=[],
    ),
    targets=[
        ImageTarget(
            repository="registry.ddbuild.io/ci/rebuildr/test-image",
            tag="latest",
            dockerfile="Dockerfile",
        ),
    ],
)
