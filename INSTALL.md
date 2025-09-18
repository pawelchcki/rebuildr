# Installation Guide

This guide covers different ways to install the `rebuildr` tool for building dependency-based Docker images.

## Prerequisites

- **Docker**: Required for building Docker images
- **Python 3.10+**: Required for running the tool
- **Skopeo**: Required for container image operations (installed automatically with Nix)

## Installation Methods

### Method 1: Docker (Recommended for Quick Setup)

The easiest way to get started is using the pre-built Docker image that contains the rebuildr tool.

#### Install from Docker Image

```bash
# Download and extract the rebuildr binary to ~/.local/bin/
docker run --rm ghcr.io/pawelchcki/rebuildr/dist:latest tool/tar | tar x -C ~/.local/bin/
```

#### Add to PATH (if not already)

Add the following line to your shell configuration file (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then reload your shell:

```bash
source ~/.bashrc  # or ~/.zshrc
```

### Method 2: Nix (Recommended for ease of use and upgrade)

If you're using Nix or NixOS, you can install rebuildr using the Nix flake.

#### Install with Nix Profile

```bash
# Install the latest version from the flake
nix profile install github:pawelchcki/rebuildr

# Or install a specific version
nix profile install github:pawelchcki/rebuildr/v0.2-dev
```

#### Install with Nix Shell (Temporary)

```bash
# Enter a shell with rebuildr available
nix shell github:pawelchcki/rebuildr

# Or add to your flake.nix inputs and use in devShells
```

#### Build from Source with Nix

```bash
# Clone the repository
git clone https://github.com/pawelchcki/rebuildr.git
cd rebuildr

# Build and install
nix profile install .#default
```

## Verification

After installation, verify that rebuildr is working correctly:

```bash
# Check version
rebuildr --version

# Run a basic command to test functionality
rebuildr load-py --help
```

You should see output similar to:

```
rebuildr load-py <rebuildr-file> [build-arg=value build-arg2=value2 ...]
```

## Next Steps

Once installed, you can:

1. Read the [README.md](README.md) for basic usage
2. Check [REBUILDR_FORMAT.md](REBUILDR_FORMAT.md) for descriptor file format
3. Look at examples in the `examples/` directory
4. See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup

## Uninstallation

### Docker Method
```bash
rm ~/.local/bin/rebuildr
```

### Nix Method
```bash
# Remove from profile
nix profile remove github:pawelchcki/rebuildr

# Or if installed from local source
nix profile remove .#default
```

## Updating

### Docker Method

To update rebuildr installed via Docker, simply re-run the installation command:

```bash
# Download and extract the latest version
docker run --rm ghcr.io/pawelchcki/rebuildr/dist:latest tool/tar | tar x -C ~/.local/bin/

```

This will overwrite the existing binary with the latest version.

### Nix Method

#### Update from Flake

```bash
# Update to the latest version from the flake
nix profile upgrade github:pawelchcki/rebuildr

# Or reinstall to get the latest
nix profile install github:pawelchcki/rebuildr --force
```

#### Update from Local Source

```bash
# Navigate to your local rebuildr directory
cd /path/to/rebuildr

# Pull the latest changes
git pull

# Reinstall with the updated code
nix profile install .#default --force
```

#### Update Nix Channels (if using channels)

```bash
# Update your Nix channels first
nix-channel --update

# Then upgrade rebuildr
nix profile upgrade github:pawelchcki/rebuildr
```

