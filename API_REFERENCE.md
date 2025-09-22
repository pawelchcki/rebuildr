# API Reference

This document provides detailed information about the Rebuildr Python API, including all classes, methods, and their usage.

## Core Classes

### `Descriptor`

The main class that defines a complete build process.

```python
from rebuildr.descriptor import Descriptor

image = Descriptor(
    inputs=Inputs(...),
    targets=[ImageTarget(...)]
)
```

**Constructor Parameters:**
- `inputs` (Inputs): Object defining all build inputs
- `targets` (Optional[list[ImageTarget]]): List of targets to build

### `Inputs`

Defines all inputs that can influence the build outcome.

```python
from rebuildr.descriptor import Inputs

inputs = Inputs(
    files=[...],
    builders=[...],
    external=[...]
)
```

**Constructor Parameters:**
- `files` (list[str | FileInput | GlobInput]): Files and directories that go into the final artifact
- `builders` (list[str | EnvInput | ArgsInput | FileInput | GlobInput]): Build tool dependencies
- `external` (list[GitHubCommitInput]): External content dependencies

### `ImageTarget`

Defines a Docker image to be built.

```python
from rebuildr.descriptor import ImageTarget

target = ImageTarget(
    repository="my-registry/myapp",
    tag="latest",
    dockerfile="Dockerfile",
)
```

**Constructor Parameters:**
- `repository` (str): Docker image repository name
- `tag` (Optional[str]): Primary tag for the image
- `also_tag_with_content_id` (bool): Whether to add content-based tags (default: True)
- `dockerfile` (Optional[str | PurePath]): Path to Dockerfile (default: "Dockerfile")
- `platform` (Optional[str | Platform]): Target platform for the build
- `target` (Optional[str]): Multi-stage Dockerfile target name

## Input Types

### `FileInput`

Represents a single file or directory.

```python
from rebuildr.descriptor import FileInput

file_input = FileInput(path="src/")
```

**Constructor Parameters:**
- `path` (str | PurePath): Path to the file or directory

### `GlobInput`

Represents files matching a glob pattern.

```python
from rebuildr.descriptor import GlobInput

glob_input = GlobInput(
    pattern="src/**/*.py",
    root_dir="."
)
```

**Constructor Parameters:**
- `pattern` (str): Glob pattern to match files
- `root_dir` (Optional[str | PurePath]): Directory to apply pattern from (default: descriptor directory)

### `EnvInput`

Represents an environment variable dependency.

```python
from rebuildr.descriptor import EnvInput

env_input = EnvInput(
    key="NODE_VERSION",
    default="18"
)
```

**Constructor Parameters:**
- `key` (str): Environment variable name
- `default` (Optional[str]): Default value if variable not set

### `ArgsInput`

Represents a build argument provided via CLI.

```python
from rebuildr.descriptor import ArgsInput

args_input = ArgsInput(
    key="VERSION",
    default="latest"
)
```

**Constructor Parameters:**
- `key` (str): Build argument name
- `default` (Optional[str]): Default value if not provided

### `GitHubCommitInput`

Represents external content from a GitHub repository.

```python
from rebuildr.descriptor import GitHubCommitInput

github_input = GitHubCommitInput(
    owner="microsoft",
    repo="vscode",
    commit="abc123def456",
    target_path="external/vscode"
)
```

**Constructor Parameters:**
- `owner` (str): GitHub organization or username
- `repo` (str): Repository name
- `commit` (str): Commit SHA to lock to
- `target_path` (str | PurePath): Path where content is considered in build

## Platform Support

### `Platform`

Enumeration of supported platforms.

```python
from rebuildr.descriptor import Platform

# Available platforms:
Platform.LINUX_AMD64    # "linux/amd64"
Platform.LINUX_ARM64    # "linux/arm64"
Platform.LINUX_ARM_V7   # "linux/arm/v7"
```

## Usage Examples

### Basic Image Build

```python
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget, FileInput

image = Descriptor(
    inputs=Inputs(
        files=[
            FileInput(path="src/"),
            FileInput(path="requirements.txt"),
        ],
        builders=[
            FileInput(path="Dockerfile"),
        ],
    ),
    targets=[
        ImageTarget(
            repository="my-registry/myapp",
            tag="latest",
            dockerfile="Dockerfile",
        )
    ]
)
```

### Multi-Platform Build

by default all builds are multiplatform

```python
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget, Platform

image = Descriptor(
    inputs=Inputs(
        files=["src/", "Dockerfile"],
    ),
    targets=[
        ImageTarget(
            repository="my-registry/myapp",
            tag="latest",
        ),
    ]
)
```

### Single-Platform Build

you have to Specify platform manually to build only a single target

```python
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget, Platform

image = Descriptor(
    inputs=Inputs(
        files=["src/", "Dockerfile"],
    ),
    targets=[
        ImageTarget(
            repository="my-registry/myapp",
            tag="latest",
            platform=Platform.LINUX_AMD64
        ),
    ]
)
```

### Environment-Dependent Build

```python
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget, EnvInput, ArgsInput

image = Descriptor(
    inputs=Inputs(
        files=["src/", "Dockerfile"],
        builders=[
            EnvInput(key="NODE_VERSION", default="18"),
            ArgsInput(key="ENV", default="production"),
            ArgsInput(key="VERSION", default="latest"),
        ],
    ),
    targets=[
        ImageTarget(
            repository="my-registry/myapp",
            tag="latest",
            dockerfile="Dockerfile",
        )
    ]
)
```

### External Dependencies

```python
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget, GitHubCommitInput

image = Descriptor(
    inputs=Inputs(
        files=["src/", "Dockerfile"],
        external=[
            GitHubCommitInput(
                owner="nodejs",
                repo="node",
                commit="abc123def456",
                target_path="external/node",
            ),
        ],
    ),
    targets=[
        ImageTarget(
            repository="my-registry/myapp",
            tag="latest",
            dockerfile="Dockerfile",
        )
    ]
)
```

### Complex File Patterns

```python
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget, GlobInput

image = Descriptor(
    inputs=Inputs(
        files=[
            GlobInput(pattern="src/**/*.py"),
            GlobInput(pattern="tests/**/*.py"),
            GlobInput(pattern="*.json"),
            "requirements.txt", # you can use simple strings they will be interpreted as FileInputs
        ],
    ),
    targets=[
        ImageTarget(
            repository="my-registry/myapp",
            tag="latest",
            dockerfile="Dockerfile",
        )
    ]
)
```

## CLI Integration

### Loading Descriptors

```python
from rebuildr.cli import load_py_desc

# Load a descriptor from file
descriptor = load_py_desc("myapp.rebuildr.py")
```

### Stable Descriptor

The `load_py_desc` function returns a `StableDescriptor` object that contains:

- **Content Hash**: Unique identifier based on all inputs
- **Image Tags**: Generated tags including content-based tags
- **Metadata**: Build information and dependencies

```python
stable_desc = load_py_desc("myapp.rebuildr.py")

# Access content hash
content_hash = stable_desc.content_hash

# Access generated tags
for target in stable_desc.targets:
    print(f"Repository: {target.repository}")
    print(f"Primary tag: {target.tag}")
    print(f"Content tag: {target.content_id_tag}")
```

## Error Handling

### Common Exceptions

```python
from rebuildr.cli import load_py_desc
import importlib.util

try:
    descriptor = load_py_desc("nonexistent.rebuildr.py")
except ImportError as e:
    print(f"Failed to load descriptor: {e}")

try:
    descriptor = load_py_desc("invalid.rebuildr.py")
except AttributeError as e:
    print(f"Descriptor missing 'image' variable: {e}")
```

### Validation

The descriptor system includes validation for:

- Required fields
- File existence
- Valid platform specifications
- Proper input types

## Best Practices

### 1. Use Specific Input Types

```python
# Good: Explicit input types
inputs = Inputs(
    files=[
        FileInput(path="src/"),
        GlobInput(pattern="*.py"),
    ],
    builders=[
        EnvInput(key="NODE_VERSION"),
        ArgsInput(key="ENV"),
    ],
)

# Avoid: String shortcuts when you need more control
inputs = Inputs(
    files=["src/", "*.py"],  # Less explicit
)
```

### 2. Leverage Content-Based Tagging

```python
ImageTarget(
    repository="my-registry/myapp",
    tag="latest",
    also_tag_with_content_id=True,  # Enables caching
)
```

### 3. Use Build Arguments for Configuration

```python
# Instead of multiple descriptors, use build arguments
inputs = Inputs(
    builders=[
        ArgsInput(key="ENV", default="production"),
        ArgsInput(key="VERSION", default="latest"),
    ],
)
```

### 4. Organize External Dependencies

```python
external_deps = [
    GitHubCommitInput(
        owner="microsoft",
        repo="vscode",
        commit="stable_commit_hash",
        target_path="external/vscode",
    ),
]
```

This API reference provides comprehensive information about using the Rebuildr Python package. For more examples and advanced usage patterns, see the examples directory and the Bazel integration guide.