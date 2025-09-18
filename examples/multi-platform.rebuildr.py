# Multi-platform Docker image build example
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget, Platform

image = Descriptor(
    inputs=Inputs(
        files=[
            "src/",
            "package.json",
            "Dockerfile",
        ],
        builders=[
            "Dockerfile",
        ],
    ),
    targets=[
        # Build for AMD64
        ImageTarget(
            repository="my-registry/webapp",
            tag="latest",
            platform=Platform.LINUX_AMD64,
            dockerfile="Dockerfile",
            also_tag_with_content_id=True,
        ),
        # Build for ARM64
        ImageTarget(
            repository="my-registry/webapp",
            tag="latest",
            platform=Platform.LINUX_ARM64,
            dockerfile="Dockerfile",
            also_tag_with_content_id=True,
        ),
    ]
)