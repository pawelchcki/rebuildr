# Bazel Integration Guide

This document explains how to use Rebuildr with Bazel, including the custom rules and their integration into your Bazel-based build system.

## Overview

Rebuildr provides several Bazel rules that allow you to integrate Docker image building into your Bazel workflow:

- `rebuildr_image`: Defines and processes a rebuildr descriptor
- `rebuildr_materialize`: Builds Docker images locally
- `rebuildr_push`: Pushes Docker images to registries
- `rebuildr_derive`: Creates variations of existing rebuildr targets

## Setup

### 1. Add Rebuildr to your WORKSPACE

Add the following to your `WORKSPACE` file:

```python
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

# Download Rebuildr
http_archive(
    name = "rebuildr",
    url = "https://github.com/pawelchcki/rebuildr/archive/main.zip",
    strip_prefix = "rebuildr-main",
    sha256 = "YOUR_SHA256_HASH",  # Update with actual hash
)

# Load Rebuildr rules
load("@rebuildr//:rebuildr.bzl", "rebuildr_image", "rebuildr_materialize", "rebuildr_push", "rebuildr_derive")
```

### 2. Create a rebuildr descriptor

Create a `.rebuildr.py` file in your project:

```python
# myapp.rebuildr.py
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget

image = Descriptor(
    inputs=Inputs(
        files=[
            "src/",
            "requirements.txt",
        ],
        builders=[
            "Dockerfile",
        ],
    ),
    targets=[
        ImageTarget(
            repository="my-registry/myapp",
            tag="latest",
            dockerfile="Dockerfile",
            also_tag_with_content_id=True,
        )
    ]
)
```

## Rules Reference

### `rebuildr_image`

The core rule that processes a rebuildr descriptor and prepares the build context.

```python
rebuildr_image(
    name = "myapp_image",
    srcs = [
        "src/",
        "requirements.txt",
        "Dockerfile",
    ],
    descriptor = "myapp.rebuildr.py",
    build_args = {
        "VERSION": "1.0.0",
        "ENV": "production",
    },
    build_env = {
        "DOCKER_BUILDKIT": "1",
    },
)
```

**Attributes:**
- `name`: A unique name for this rule
- `srcs`: Source files to include in the build context
- `descriptor`: The `.rebuildr.py` file defining the build
- `build_args`: Docker build arguments (optional)
- `build_env`: Environment variables for the build (optional)

**Outputs:**
- `{name}.stable`: Stable metadata file
- `{name}.stable_image_tag`: Content-based image tag
- `{name}.work_dir`: Working directory with copied files

### `rebuildr_materialize`

Builds Docker images locally using the processed descriptor.

```python
rebuildr_materialize(
    name = "myapp_materialize",
    src = ":myapp_image",
)
```

**Attributes:**
- `name`: A unique name for this rule
- `src`: The `rebuildr_image` target to materialize

**Outputs:**
- `{name}.out`: Build output log

### `rebuildr_push`

Pushes Docker images to a registry.

```python
rebuildr_push(
    name = "myapp_push",
    src = ":myapp_image",
)
```

**Attributes:**
- `name`: A unique name for this rule
- `src`: The `rebuildr_image` target to push

**Outputs:**
- `{name}.pushed`: Push completion marker

### `rebuildr_derive`

Creates variations of existing rebuildr targets with different build arguments or environment variables.

```python
rebuildr_derive(
    name = "myapp_dev",
    src = ":myapp_image",
    build_args = {
        "ENV": "development",
    },
    build_env = {
        "DEBUG": "1",
    },
)
```

**Attributes:**
- `name`: A unique name for this rule
- `src`: The `rebuildr_image` target to derive from
- `build_args`: Additional build arguments (optional)
- `build_env`: Additional environment variables (optional)

## Complete Example

Here's a complete example showing how to use all the rules together:

```python
# BUILD.bazel
load("@rebuildr//:rebuildr.bzl", "rebuildr_image", "rebuildr_materialize", "rebuildr_push", "rebuildr_derive")

# Base image definition
rebuildr_image(
    name = "webapp_image",
    srcs = [
        "src/",
        "package.json",
        "Dockerfile",
    ],
    descriptor = "webapp.rebuildr.py",
    build_args = {
        "NODE_VERSION": "18",
    },
)

# Development variant
rebuildr_derive(
    name = "webapp_dev",
    src = ":webapp_image",
    build_args = {
        "ENV": "development",
    },
)

# Production variant
rebuildr_derive(
    name = "webapp_prod",
    src = ":webapp_image",
    build_args = {
        "ENV": "production",
    },
)

# Build development image
rebuildr_materialize(
    name = "webapp_dev_build",
    src = ":webapp_dev",
)

# Build production image
rebuildr_materialize(
    name = "webapp_prod_build",
    src = ":webapp_prod",
)

# Push production image
rebuildr_push(
    name = "webapp_prod_push",
    src = ":webapp_prod",
)
```

## Usage Commands

### Build an image locally
```bash
bazel run //path/to:webapp_dev_build
```

### Push an image to registry
```bash
bazel run //path/to:webapp_prod_push
```

### Get stable metadata
```bash
bazel build //path/to:webapp_image
cat bazel-bin/path/to/webapp_image.stable
```

## Best Practices

### 1. Organize your BUILD files

Structure your BUILD files to separate concerns:

```python
# apps/webapp/BUILD.bazel
rebuildr_image(
    name = "webapp_image",
    srcs = glob(["src/**/*"]) + ["Dockerfile"],
    descriptor = "webapp.rebuildr.py",
)

# apps/webapp/dev/BUILD.bazel
rebuildr_derive(
    name = "webapp_dev",
    src = "//apps/webapp:webapp_image",
    build_args = {"ENV": "development"},
)

rebuildr_materialize(
    name = "webapp_dev_build",
    src = ":webapp_dev",
)
```

### 2. Use build arguments for configuration

Instead of creating separate descriptors for different environments, use build arguments:

```python
# webapp.rebuildr.py
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget, ArgsInput

image = Descriptor(
    inputs=Inputs(
        files=["src/", "Dockerfile"],
        builders=[
            ArgsInput(key="ENV", default="production"),
            ArgsInput(key="VERSION", default="latest"),
        ],
    ),
    targets=[
        ImageTarget(
            repository="my-registry/webapp",
            tag="latest",
            dockerfile="Dockerfile",
        )
    ]
)
```

### 3. Leverage content-based tagging

Enable `also_tag_with_content_id=True` to get content-addressable tags:

```python
ImageTarget(
    repository="my-registry/webapp",
    tag="latest",
    also_tag_with_content_id=True,  # Creates additional tag like: linux-amd64-src-id-abc123
    dockerfile="Dockerfile",
)
```

## Troubleshooting

### Common Issues

1. **File not found errors**: Ensure all files referenced in `srcs` exist and are accessible
2. **Descriptor parsing errors**: Check that your `.rebuildr.py` file exports an `image` variable
3. **Docker build failures**: Verify that Docker is running and accessible
4. **Registry push failures**: Ensure you're authenticated with the target registry

### Debug Commands

```bash
# Check what files are being copied
bazel build //path/to:target --verbose_failures

# Inspect the working directory
bazel build //path/to:target
ls -la bazel-bin/path/to/target.work_dir/

# Check stable metadata
cat bazel-bin/path/to/target.stable
```

## Integration with Other Bazel Rules

Rebuildr rules can be combined with other Bazel rules:

```python
# Use with filegroup for better file management
filegroup(
    name = "webapp_sources",
    srcs = glob(["src/**/*"]),
)

rebuildr_image(
    name = "webapp_image",
    srcs = [":webapp_sources", "Dockerfile"],
    descriptor = "webapp.rebuildr.py",
)

# Use with genrule for preprocessing
genrule(
    name = "generate_config",
    srcs = ["config.template"],
    outs = ["config.json"],
    cmd = "sed 's/VERSION/$(VERSION)/g' $< > $@",
)

rebuildr_image(
    name = "webapp_image",
    srcs = [":webapp_sources", ":generate_config", "Dockerfile"],
    descriptor = "webapp.rebuildr.py",
)
```

This integration allows you to leverage Bazel's powerful dependency management and caching while using Rebuildr's reproducible Docker image building capabilities.