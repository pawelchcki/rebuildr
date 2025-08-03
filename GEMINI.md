# Gemini Code Understanding

This document provides an overview of the `rebuildr` project, its structure, and how to build and interact with it.

## Project Overview

`rebuildr` is a Python-based tool for building Docker images and other artifacts in a reproducible way. It uses special Python script files with a `.rebuildr.py` extension to define the build process.

The core concepts of `rebuildr` are:

*   **Declarative Builds**: Build definitions are Python scripts that create a `Descriptor` object. This object specifies all inputs (source files, environment variables) and targets (Docker images, tar files).
*   **Content-Addressable Tagging**: `rebuildr` can tag Docker images with a unique ID based on the hash of its contents. This ensures that identical builds result in identical image tags, which is useful for caching and reproducibility.
*   **Bazel Integration**: The `rebuildr` project itself is built using the Bazel build system. It defines custom Bazel rules (e.g., `rebuildr_image`) to integrate `rebuildr` into a Bazel-based workflow.

## Building and Running

There are three main ways to interact with this project: using the `rebuildr` command-line tool directly, building the project with Bazel, or using the Nix development environment. For most development tasks, the Nix workflow is preferred as it provides a consistent and reproducible environment.

### Using the `rebuildr` CLI

The `rebuildr` command-line tool is the primary way to use the system. The entry point is defined in `pyproject.toml` and implemented in `rebuildr/cli.py`.

**Key Commands:**

*   `rebuildr load-py <rebuildr-file>`: Parses a `.rebuildr.py` file and prints its stable descriptor as a JSON object.
*   `rebuildr load-py <rebuildr-file> materialize-image`: Builds a Docker image from the given `.rebuildr.py` file.
*   `rebuildr load-py <rebuildr-file> push-image`: Builds and pushes a Docker image to a registry.
*   `rebuildr load-py <rebuildr-file> build-tar <output>`: Creates a tar archive from the specified inputs.

### Building with Bazel

The project uses Bazel for its own build process. The `.bazelrc` file contains common configuration options.

**Key Bazel Targets:**

*   You can build the `rebuildr` tool itself by running `bazel build //rebuildr:rebuildr`.
*   The project defines a custom Bazel rule `rebuildr_image` in `bzl/rule/image.bzl`. This rule can be used in `BUILD.bazel` files to define how to build Docker images using `rebuildr`.

### Using Nix

This project provides a Nix flake for setting up a consistent development environment. To use it, you need to have Nix installed with flake support enabled.

**Key Commands:**

*   `nix develop`: Activates a development shell with all the necessary dependencies, including `uv`, `bazel`, and `jdk`.
*   `uv run pytest`: Once inside the development shell, you can run the test suite using `uv run pytest`.
*   `nix build`: Builds the `rebuildr` package using Nix.

The Nix flake also configures `pre-commit-hooks` to ensure code quality and consistency.

## Development Conventions

*   **Build Definitions**: All build logic is defined in `.rebuildr.py` files. These files must contain a variable named `image` which is an instance of the `Descriptor` class. See `REBUILDR_FORMAT.md` for a detailed explanation of the format.
*   **Python Project Structure**: The project follows standard Python packaging conventions, with all source code in the `rebuildr` directory. It uses `pyproject.toml` to manage project metadata and dependencies.
*   **Testing**: Tests are located in the `tests` directory and can be run with `pytest`.
*   **Bazel for Build**: The project is built and managed with Bazel. All dependencies and build rules are defined in `BUILD.bazel` files.
