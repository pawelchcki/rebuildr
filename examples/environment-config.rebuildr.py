# Environment-dependent configuration example
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget, EnvInput, ArgsInput

image = Descriptor(
    inputs=Inputs(
        files=[
            "src/",
            "config/",
            "Dockerfile",
        ],
        builders=[
            # Environment variables that affect the build
            EnvInput(key="NODE_VERSION", default="18"),
            EnvInput(key="NPM_REGISTRY", default="https://registry.npmjs.org/"),
            
            # Build arguments for configuration
            ArgsInput(key="ENV", default="production"),
            ArgsInput(key="VERSION", default="latest"),
            ArgsInput(key="DEBUG", default="false"),
        ],
    ),
    targets=[
        ImageTarget(
            repository="my-registry/webapp",
            tag="latest",
            dockerfile="Dockerfile",
            also_tag_with_content_id=True,
        )
    ]
)