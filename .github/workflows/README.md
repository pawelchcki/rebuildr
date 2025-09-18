# GitHub Actions Workflows

This directory contains GitHub Actions workflows that use Determinate Systems Nix actions for CI/CD.

## Workflows

### 1. CI (`ci.yml`)
Main continuous integration workflow that runs on every push and pull request.

**Jobs:**
- **Format Check**: Runs `treefmt --check` to verify code formatting
- **Pre-commit Check**: Runs pre-commit hooks defined in the flake
- **Test**: Runs Python tests using pytest
- **Build**: Builds the main package and Docker image
- **Build Matrix**: Multi-platform builds for all supported systems
- **Dev Shell**: Verifies the development environment works correctly

**Supported Platforms:**
- `x86_64-linux` (Ubuntu)
- `x86_64-darwin` (macOS)
- `aarch64-linux` (Ubuntu)
- `aarch64-darwin` (macOS)

### 2. Release (`release.yml`)
Handles release builds when tags are pushed.

**Jobs:**
- **Pre-release Checks**: Runs all checks before building release artifacts
- **Build Release**: Creates release artifacts for the main platform
- **Build Release Matrix**: Creates release artifacts for all supported platforms

**Triggers:**
- Push to tags matching `v*` pattern

### 3. Dependencies (`dependencies.yml`)
Manages dependency updates and security audits.

**Jobs:**
- **Update Flake Inputs**: Weekly update of Nix flake inputs with automatic PR creation
- **Security Audit**: Checks for security vulnerabilities
- **Dependency Freshness**: Reports on dependency freshness

**Schedule:**
- Runs weekly on Mondays at 2 AM UTC
- Can be triggered manually via `workflow_dispatch`

### 4. Compatibility (`compatibility.yml`)
Tests compatibility across different versions and environments.

**Jobs:**
- **Nix Versions**: Tests with different Nix versions (2.18, 2.19, 2.20)
- **Python Versions**: Tests with different Python versions (3.10, 3.11, 3.12)
- **Bazel Compatibility**: Tests Bazel build and test commands
- **Docker Compatibility**: Tests Docker image creation and execution

**Schedule:**
- Runs weekly on Sundays at 3 AM UTC
- Also runs on push/PR to main branches

## Key Features

### Determinate Systems Nix Actions
All workflows use Determinate Systems Nix actions for:
- **Fast Nix installation**: `DeterminateSystems/nix-installer-action@v9`
- **Efficient flake dependency caching**: `DeterminateSystems/flake-checking-action@v1`

### Comprehensive Testing
- Code formatting with `treefmt`
- Pre-commit hooks validation
- Python unit tests
- Multi-platform builds
- Docker image verification
- Bazel build system testing

### Automated Maintenance
- Weekly flake input updates
- Security vulnerability scanning
- Dependency freshness monitoring
- Compatibility testing across versions

## Usage

### Running Locally
You can run the same checks locally using Nix:

```bash
# Format check
nix run .#formatter -- --check

# Pre-commit checks
nix run .#checks.pre-commit-check

# Run tests
nix run .#checks.default

# Build package
nix build .#default

# Build Docker image
nix build .#docker-image
```

### Manual Workflow Triggers
Some workflows can be triggered manually:
- **Dependencies**: Update flake inputs and run security audits
- **Compatibility**: Test across different versions

### Customization
To customize the workflows:
1. Modify the matrix configurations for different platforms/versions
2. Add additional checks in the appropriate workflow files
3. Update the flake inputs list in `flake-checking-action` steps
4. Adjust schedules in the `on.schedule` sections

## Requirements

- Nix flake with proper `checks` and `formatter` outputs
- Pre-commit hooks configuration
- Treefmt configuration for code formatting
- Python project with pytest tests