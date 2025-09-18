# Rebuildr Examples

This directory contains various examples demonstrating different use cases and features of Rebuildr.

## Basic Examples

### `first.rebuildr.py`
A simple example showing the basic structure of a rebuildr descriptor file.

**Usage:**
```bash
rebuildr load-py examples/first.rebuildr.py
rebuildr load-py examples/first.rebuildr.py materialize-image
```

### `to-tar.rebuildr.py`
Example of creating a tar archive instead of a Docker image.

**Usage:**
```bash
rebuildr load-py examples/to-tar.rebuildr.py build-tar output.tar
```

## Advanced Examples

### `multi-platform.rebuildr.py`
Demonstrates building Docker images for multiple platforms (AMD64 and ARM64).

**Features:**
- Multi-platform builds
- Content-based tagging
- Platform-specific image tags

**Usage:**
```bash
rebuildr load-py examples/multi-platform.rebuildr.py materialize-image
```

### `environment-config.rebuildr.py`
Shows how to use environment variables and build arguments for configuration.

**Features:**
- Environment variable dependencies
- Build argument configuration
- Default values for configuration

**Usage:**
```bash
# With default values
rebuildr load-py examples/environment-config.rebuildr.py materialize-image

# With custom values
rebuildr load-py examples/environment-config.rebuildr.py ENV=development VERSION=1.0.0 DEBUG=true materialize-image
```

### `external-deps.rebuildr.py`
Example of using external dependencies from GitHub repositories.

**Features:**
- GitHub commit pinning
- External content management
- Reproducible builds with external dependencies

**Usage:**
```bash
rebuildr load-py examples/external-deps.rebuildr.py materialize-image
```

**Note:** Replace the commit hashes with actual commit SHAs from the repositories.

### `complex-patterns.rebuildr.py`
Demonstrates complex file pattern matching using glob patterns.

**Features:**
- Glob pattern matching
- Multiple file types
- Selective file inclusion

**Usage:**
```bash
rebuildr load-py examples/complex-patterns.rebuildr.py materialize-image
```

### `multi-stage.rebuildr.py`
Example of using multi-stage Dockerfiles with different targets.

**Features:**
- Multi-stage Docker builds
- Different targets (production, development)
- Multiple image variants

**Usage:**
```bash
# Build production image
rebuildr load-py examples/multi-stage.rebuildr.py materialize-image

# Build development image (requires Dockerfile.multi-stage)
rebuildr load-py examples/multi-stage.rebuildr.py materialize-image
```

## Dockerfiles

### `first.Dockerfile`
Simple Dockerfile for the basic example.

### `Dockerfile.multi-stage`
Multi-stage Dockerfile with separate development and production stages.

### `webapp.Dockerfile`
Production-ready Dockerfile with security best practices.

## Running Examples

### Prerequisites

1. **Docker**: Ensure Docker is running
2. **Rebuildr**: Install rebuildr (see [INSTALL.md](../INSTALL.md))

### Basic Testing

```bash
# Test descriptor parsing
rebuildr load-py examples/first.rebuildr.py

# Test image building
rebuildr load-py examples/first.rebuildr.py materialize-image

# Test with build arguments
rebuildr load-py examples/environment-config.rebuildr.py ENV=test materialize-image
```

### Advanced Testing

```bash
# Test multi-platform builds
rebuildr load-py examples/multi-platform.rebuildr.py materialize-image

# Test external dependencies (update commit hashes first)
rebuildr load-py examples/external-deps.rebuildr.py materialize-image

# Test complex patterns
rebuildr load-py examples/complex-patterns.rebuildr.py materialize-image
```

## Bazel Integration

These examples can also be used with Bazel integration:

```python
# BUILD.bazel
load("@rebuildr//:rebuildr.bzl", "rebuildr_image", "rebuildr_materialize")

rebuildr_image(
    name = "webapp_image",
    srcs = glob(["src/**/*"]) + ["Dockerfile"],
    descriptor = "webapp.rebuildr.py",
)

rebuildr_materialize(
    name = "webapp_build",
    src = ":webapp_image",
)
```

## Customizing Examples

### Adding Your Own Files

1. Create your own `.rebuildr.py` file
2. Update the `files` list in the `Inputs`
3. Ensure all referenced files exist
4. Test with `rebuildr load-py your-file.rebuildr.py`

### Environment Variables

Set environment variables to affect builds:

```bash
export NODE_VERSION=20
export NPM_REGISTRY=https://registry.npmjs.org/
rebuildr load-py examples/environment-config.rebuildr.py materialize-image
```

### Build Arguments

Pass build arguments for configuration:

```bash
rebuildr load-py examples/environment-config.rebuildr.py \
  ENV=production \
  VERSION=2.0.0 \
  DEBUG=false \
  materialize-image
```

## Troubleshooting

### Common Issues

1. **File not found**: Ensure all files referenced in descriptors exist
2. **Docker errors**: Check that Docker is running and accessible
3. **Permission issues**: Ensure you have permission to build Docker images

### Debug Commands

```bash
# Check descriptor parsing
rebuildr load-py examples/first.rebuildr.py

# Verbose output
rebuildr load-py examples/first.rebuildr.py --verbose

# Check Docker status
docker info
```

For more troubleshooting help, see [TROUBLESHOOTING.md](../TROUBLESHOOTING.md).

## Contributing Examples

When adding new examples:

1. **Follow naming convention**: Use descriptive names ending in `.rebuildr.py`
2. **Include documentation**: Add comments explaining the example
3. **Test thoroughly**: Ensure examples work as expected
4. **Update this README**: Add your example to the appropriate section

## Related Documentation

- [API Reference](../API_REFERENCE.md): Detailed API documentation
- [Bazel Integration](../BAZEL_INTEGRATION.md): Using rebuildr with Bazel
- [Troubleshooting](../TROUBLESHOOTING.md): Common issues and solutions
- [Installation Guide](../INSTALL.md): How to install rebuildr