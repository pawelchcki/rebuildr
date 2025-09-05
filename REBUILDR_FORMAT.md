
# Rebuildr File Format (`<name>.rebuildr.py`)

The `<name>.rebuildr.py` file is a Python script that defines a build process for `rebuildr`. The core of this file is the creation of a `Descriptor` object, which is assigned to a variable named `image`. This `Descriptor` object specifies all the inputs required for the build and the targets to be produced.

Every file must export the descriptor via `image` variable.

## High-Level Structure

A typical `<name>.rebuildr.py` file has the following structure:

1.  **Imports**: Import necessary classes like `Descriptor`, `Inputs`, and `ImageTarget` from `rebuildr.descriptor`.
2.  **Instantiation**: Create an instance of the `Descriptor` class.
3.  **Assignment**: Assign the created `Descriptor` instance to a variable named `image`.

### Example

```python
# my_project.rebuildr.py

from rebuildr.descriptor import Descriptor, Inputs, ImageTarget

image = Descriptor(
    inputs=Inputs(
        # List of files and directories that affect the build
        files=[
            "src/",
            "requirements.txt",
        ]
    ),
    targets=[
        ImageTarget(
            repository="my-docker-registry/my-app",
            tag="latest",
            dockerfile="Dockerfile.prod",
            also_tag_with_content_id=True
        )
    ]
)
```

## Core Components

### `Descriptor`

The `Descriptor` is the main object that encapsulates the entire build definition.

| Field     | Type                     | Description                                            |
| :-------- | :----------------------- | :----------------------------------------------------- |
| `inputs`  | `Inputs`                 | An object defining all the inputs for the build.       |
| `targets` | `Optional[list[ImageTarget]]` | A list of targets to be built, typically Docker images. |

---

### `Inputs`

The `Inputs` object specifies all the files, environment variables, and other data that can influence the build outcome. This is crucial for `rebuildr` to determine if a rebuild is necessary.

| Field      | Type                                                     | Description                                                                                                                                                 |
| :--------- | :------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `files`    | `list[str | FileInput | GlobInput]`                      | A list of files or directories. Can be simple strings (paths), `FileInput` objects, or `GlobInput` objects for pattern-based file matching.                 |
| `builders` | `list[str | EnvInput | ArgsInput | FileInput | GlobInput]` | Inputs that affect the build tool or process itself (e.g., environment variables, build args, or tool configuration files).                                  |
| `external` | `list[GitHubCommitInput]`                                | External content dependencies that affect the build, currently only GitHub commit inputs are supported.                                                     |

#### Input Types

-   **String**: A simple string can be used as a shortcut for a `FileInput`. `files=["src/"]` is equivalent to `files=[FileInput(path="src/")]`.
-   **`FileInput`**: Represents a single file or directory.
    -   `path: str | PurePath` - The path to the file or directory.
-   **`GlobInput`**: Represents a set of files matching a glob pattern.
    -   `pattern: str` - The glob pattern (e.g., `src/**/*.py`).
    -   `root_dir: Optional[str | PurePath]` - The directory from which to apply the glob pattern. Defaults to the directory of the `.rebuildr.py` file.
-   **`EnvInput`**: Represents an environment variable.
    -   `key: str` - The name of the environment variable.
    -   `default: Optional[str]` - A default value to use if the environment variable is not set.

-   **`ArgsInput`**: Represents a build argument value provided on the CLI. When present, the key and its value participate in the content hash.
    -   `key: str` - The name of the build argument (e.g., `VERSION`).
    -   `default: Optional[str]` - A default value to use if no CLI value is provided.

-   **`GitHubCommitInput`**: Represents external content fixed to a specific Git commit.
    -   `owner: str` - GitHub organization or user name.
    -   `repo: str` - Repository name.
    -   `commit: str` - Commit SHA to lock to.
    -   `target_path: str | PurePath` - Path where this external content is considered in the build inputs.

---

### `ImageTarget`

An `ImageTarget` defines a Docker image that should be built.

| Field                      | Type                           | Description                                                                                                                                                 |
| :------------------------- | :----------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `repository`               | `str`                          | The Docker image repository name (e.g., `my-username/my-app`).                                                                                              |
| `tag`                      | `Optional[str]`                | The primary tag for the image (e.g., `latest`, `v1.2.0`).                                                                                                   |
| `also_tag_with_content_id` | `bool`                         | If `True` (default), the image will also be tagged with a unique ID based on the hash of its contents. Useful for content-addressable storage and caching. |
| `dockerfile`               | `Optional[str | PurePath]`     | The path to the Dockerfile. Defaults to `Dockerfile` if not specified.                                                                                      |
| `platform`                 | `Optional[str | Platform]`     | Target platform for the build (e.g., `"linux/amd64"` or `"linux/arm64"`). If set, the content-id tag is prefixed with the platform.                      |
| `target`                   | `Optional[str]`                | The name of the target build stage in a multi-stage Dockerfile. Currently ignored at build time.                                                            |

Notes:

- When `platform` is not specified, builds default to `linux/amd64,linux/arm64` and the content-id tag is not platform-prefixed.
- When `platform` is specified, the generated content-id tag is prefixed with the platform (slashes replaced by dashes), for example: `linux-amd64-src-id-<hash>`.

By combining these components, you can create a declarative build definition that `rebuildr` can use to build your artifacts reproducibly. 