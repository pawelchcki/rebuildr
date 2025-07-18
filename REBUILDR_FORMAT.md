
# Rebuildr File Format (`<name>.rebuildr.py`)

The `<name>.rebuildr.py` file is a Python script that defines a build process for `rebuildr`. The core of this file is the creation of a `Descriptor` object, which is assigned to a variable named `image`. This `Descriptor` object specifies all the inputs required for the build and the targets to be produced.

Every file requires to export the describtor via `image` variable.

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

| Field      | Type                                     | Description                                                                                                                              |
| :--------- | :--------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------- |
| `files`    | `list[str | FileInput | GlobInput]`     | A list of files or directories. Can be simple strings (paths), `FileInput` objects, or `GlobInput` objects for pattern-based file matching.    |
| `builders` | `list[str | EnvInput | FileInput | GlobInput]` | A list of inputs that affect the build process itself, such as environment variables that configure a build tool, or the build tool's own configuration files. |

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

---

### `ImageTarget`

An `ImageTarget` defines a Docker image that should be built.

| Field                      | Type                 | Description                                                                                             |
| :------------------------- | :------------------- | :------------------------------------------------------------------------------------------------------ |
| `repository`               | `str`                | The Docker image repository name (e.g., `my-username/my-app`).                                          |
| `tag`                      | `Optional[str]`      | The primary tag for the image (e.g., `latest`, `v1.2.0`).                                               |
| `also_tag_with_content_id` | `bool`               | If `True` (default), the image will also be tagged with a unique ID based on the hash of its contents. This is useful for content-addressable storage and caching. |
| `dockerfile`               | `Optional[str | PurePath]` | The path to the Dockerfile to be used for building the image.                                           |
| `target`                   | `Optional[str]`      | The name of the target build stage in a multi-stage Dockerfile. (Note: Not fully supported yet).          |

By combining these components, you can create a declarative build definition that `rebuildr` can use to build your artifacts reproducibly. 