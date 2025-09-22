# Rebuildr

Rebuildr is a powerful tool for building reproducible Docker images with dependency-based caching. It uses Python descriptor files to define build processes and integrates seamlessly with Bazel for large-scale builds.

## Features

- **Reproducible Builds**: Content-addressable image tagging ensures identical builds produce identical tags
- **Dependency Tracking**: Automatically tracks all inputs (files, environment variables, external dependencies) to determine when rebuilds are necessary
- **Bazel Integration**: Custom Bazel rules for seamless integration into existing build systems
- **Multi-Platform Support**: Build for multiple architectures (AMD64, ARM64) with platform-specific tagging
- **External Dependencies**: Pin external content (GitHub repositories) to specific commits for reproducible builds
- **Flexible Input Types**: Support for files, glob patterns, environment variables, and build arguments

## Quick Start

### Installation

```bash
# Using Docker (recommended for quick setup)
docker run --rm ghcr.io/pawelchcki/rebuildr/dist:latest tool/tar | tar x -C ~/.local/bin/

# Using Nix (recommended for development)
nix profile install github:pawelchcki/rebuildr
```

### Basic Usage

1. **Create a descriptor file** (`myapp.rebuildr.py`):
```python
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget

image = Descriptor(
    inputs=Inputs(
        files=["src/", "Dockerfile"],
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

2. **Build the image**:
```bash
rebuildr load-py myapp.rebuildr.py materialize-image
```

## Bazel Integration

Rebuildr provides custom Bazel rules for seamless integration:

```python
# BUILD.bazel
load("@rebuildr//:rebuildr.bzl", "rebuildr_image", "rebuildr_materialize")

rebuildr_image(
    name = "webapp_image",
    srcs = glob(["src/**/*"]) + ["Dockerfile"],
    descriptor = "webapp.rebuildr.py",
    build_args = {"VERSION": "1.0.0"},
)

rebuildr_materialize(
    name = "webapp_build",
    src = ":webapp_image",
)
```

Build with: `bazel run //path/to:webapp_build`

## Documentation

- **[Installation Guide](INSTALL.md)**: Detailed installation instructions
- **[File Format](REBUILDR_FORMAT.md)**: Complete descriptor file format reference
- **[API Reference](API_REFERENCE.md)**: Python API documentation
- **[Bazel Integration](BAZEL_INTEGRATION.md)**: Using rebuildr with Bazel
- **[Examples](examples/)**: Comprehensive examples and use cases
- **[Troubleshooting](TROUBLESHOOTING.md)**: Common issues and solutions
- **[Contributing](CONTRIBUTING.md)**: Development setup and contribution guidelines

## Installation

Quick start:

```bash
# Via Docker (recommended)
docker run --rm ghcr.io/pawelchcki/rebuildr/dist:latest tool/tar | tar x -C ~/.local/bin/

# Via Nix
nix profile install github:pawelchcki/rebuildr
```

For other installation methods, updates, and info on verifying your setup, refer to [INSTALL.md](INSTALL.md).

## Contributing

We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for environment setup, coding style, and tips to get started.

## CLI Interface

Rebuildr provides a command-line interface for parsing, building, and managing Docker images based on rebuildr descriptor files.

### Usage

```
rebuildr <command> <args>
```

### Commands

#### `load-py` - Parse and work with rebuildr descriptor files

**Basic parsing** (outputs JSON metadata):
```bash
rebuildr load-py <rebuildr-file> [build-arg=value build-arg2=value2 ...]
```

**Generate Bazel stable metadata**:
```bash
rebuildr load-py <rebuildr-file> [build-arg=value ...] bazel-stable-metadata <stable-metadata-file> <stable-image-tag-file>
```

**Materialize Docker image**:
```bash
rebuildr load-py <rebuildr-file> [build-arg=value ...] materialize-image
```

**Build and push Docker image**:
```bash
rebuildr load-py <rebuildr-file> [build-arg=value ...] push-image [<override-tag>]
```

If `<override-tag>` is provided, the built image will be re-tagged to that value and the override tag will be pushed instead.

**Build tar archive**:
```bash
rebuildr load-py <rebuildr-file> build-tar <output-file>
```

### Build Arguments

Build arguments can be passed to any `load-py` command using the format `key=value`. Multiple build arguments can be specified:

```bash
rebuildr load-py my-image.rebuildr.py ARG1=value1 ARG2=value2 materialize-image
```

Build arguments are used by `ArgsInput` entries in your rebuildr descriptor and affect the content hash of the resulting image.

### Environment Variables

- `REBUILDR_OVERRIDE_ROOT_DIR`: When set, overrides the root directory used to resolve inputs in the descriptor. Useful when executing from a different working directory than the descriptor's location.
- `DOCKER_QUIET`: When set (any value), reduces Docker build output noise in the terminal.

### Platforms and Content-ID Tags

- If an `ImageTarget.platform` is set (e.g., `"linux/amd64"` or `"linux/arm64"`), the generated content-id tag is prefixed with the platform (slashes replaced by dashes), e.g., `linux-amd64-src-id-<hash>`.
- If `platform` is not set, builds default to `linux/amd64,linux/arm64` and the content-id tag does not include a platform prefix.

### Examples

Parse a rebuildr file and output metadata:
```bash
rebuildr load-py examples/first.rebuildr.py
```

Build a Docker image with build arguments:
```bash
rebuildr load-py examples/first.rebuildr.py VERSION=1.0 ENV=prod materialize-image
```

Create a tar archive:
```bash
rebuildr load-py examples/to-tar.rebuildr.py build-tar output.tar
```
