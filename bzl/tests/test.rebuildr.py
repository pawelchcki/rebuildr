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
            repository="test-image",
            tag="latest",
            dockerfile="Dockerfile",
        ),
    ],
)
