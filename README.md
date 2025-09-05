# Rebuildr

Tool used for mass building dependency based docker images

Work In progress

See: REBUILDR_FORMAT.md for file format description

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
rebuildr load-py <rebuildr-file> [build-arg=value ...] push-image
```

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