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