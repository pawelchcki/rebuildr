# External dependencies example
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget, GitHubCommitInput

image = Descriptor(
    inputs=Inputs(
        files=[
            "src/",
            "Dockerfile",
        ],
        external=[
            # Pin external dependencies to specific commits
            GitHubCommitInput(
                owner="microsoft",
                repo="vscode",
                commit="abc123def456789",  # Replace with actual commit hash
                target_path="external/vscode",
            ),
            GitHubCommitInput(
                owner="nodejs",
                repo="node",
                commit="def456ghi789012",  # Replace with actual commit hash
                target_path="external/node",
            ),
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