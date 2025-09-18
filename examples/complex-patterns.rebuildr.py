# Complex file patterns example
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget, GlobInput, FileInput

image = Descriptor(
    inputs=Inputs(
        files=[
            # Include all Python files
            GlobInput(pattern="src/**/*.py"),
            
            # Include all configuration files
            GlobInput(pattern="config/**/*.json"),
            GlobInput(pattern="config/**/*.yaml"),
            GlobInput(pattern="config/**/*.yml"),
            
            # Include specific files
            FileInput(path="requirements.txt"),
            FileInput(path="Dockerfile"),
            
            # Include documentation
            GlobInput(pattern="docs/**/*.md"),
            
            # Include tests
            GlobInput(pattern="tests/**/*.py"),
        ],
        builders=[
            # Build tool dependencies
            FileInput(path="Dockerfile"),
            GlobInput(pattern="scripts/**/*.sh"),
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