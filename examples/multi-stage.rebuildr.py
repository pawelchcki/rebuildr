# Multi-stage Dockerfile example
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget

image = Descriptor(
    inputs=Inputs(
        files=[
            "src/",
            "package.json",
            "package-lock.json",
            "Dockerfile.multi-stage",
        ],
        builders=[
            "Dockerfile.multi-stage",
        ],
    ),
    targets=[
        # Build the final production image
        ImageTarget(
            repository="my-registry/webapp",
            tag="latest",
            dockerfile="Dockerfile.multi-stage",
            target="production",  # Target the production stage
            also_tag_with_content_id=True,
        ),
        # Also build the development image
        ImageTarget(
            repository="my-registry/webapp",
            tag="dev",
            dockerfile="Dockerfile.multi-stage",
            target="development",  # Target the development stage
            also_tag_with_content_id=True,
        ),
    ]
)