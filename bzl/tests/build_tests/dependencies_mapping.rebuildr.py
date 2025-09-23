from rebuildr.descriptor import (
    Descriptor,
    GlobInput,
    Inputs,
    ImageTarget,
)

image = Descriptor(
    inputs=Inputs(
        files=[GlobInput(pattern="**/*")],
    ),
    targets=[
        ImageTarget(
            repository="test123",
            tag="v0",
            dockerfile="dependencies_mapping.Dockerfile",
            platform="linux/amd64",
        ),
    ],
)
