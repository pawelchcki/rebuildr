# Contributing to Rebuildr

First off, thank you for considering contributing to Rebuildr! It's people like you that will make rebuildr the future of building docker images.

## How to Contribute

We welcome contributions in many forms:

- **Bug reports**: Help us identify and fix issues
- **Feature requests**: Suggest new functionality
- **Code contributions**: Submit pull requests with improvements
- **Documentation**: Help improve our guides and examples
- **Testing**: Add tests or help test new features

## Setting Up the Development Environment

We use [Nix](https://nixos.org/) to provide a consistent development environment across all platforms.

### Prerequisites

- **Nix**: Required for the development environment
- **Docker**: Required for testing Docker image builds
- **Git**: For version control

### Installation Steps

1. **Install Nix**: Follow the instructions on the [official Nix website](https://nixos.org/download.html) to install Nix on your system.

2. **Enable Flakes**: Make sure you have Nix Flakes enabled. You can do this by adding the following to your Nix configuration file (`~/.config/nix/nix.conf`):
   ```
   experimental-features = nix-command flakes
   ```

3. **Clone the Repository**: 
   ```bash
   git clone https://github.com/pawelchcki/rebuildr.git
   cd rebuildr
   ```

4. **Enter the Development Shell**: Run `nix develop` in the project root. This will drop you into a shell with all the necessary dependencies including:
   - Python 3.10+
   - uv (Python package manager)
   - Bazel
   - Docker
   - Git

5. **[OPTIONAL] Install Python dependencies manually**: If you prefer not to use Nix, you can use `uv` to manage Python dependencies:
   ```bash
   uv sync
   ```

Now you should be all set to start developing!

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_specific.py

# Run tests with coverage
uv run pytest --cov=rebuildr
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Format code
treefmt

# Run linting
uv run ruff check .

# Fix linting issues
uv run ruff check --fix .
```

### Building the Project

```bash
# Build with Bazel
bazel build //rebuildr:rebuildr

# Build with Nix
nix build
```

### Testing Docker Functionality

```bash
# Test basic functionality
rebuildr load-py examples/first.rebuildr.py

# Test image building
rebuildr load-py examples/first.rebuildr.py materialize-image

# Test with build arguments
rebuildr load-py examples/first.rebuildr.py VERSION=1.0 materialize-image
```

## Making Changes

### Before You Start

1. **Check existing issues**: Look for similar issues or feature requests
2. **Create an issue**: For significant changes, create an issue to discuss the approach
3. **Fork the repository**: Create your own fork to work on

### Development Process

1. **Create a branch**: 
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**: Follow the coding standards and add tests

3. **Test your changes**:
   ```bash
   # Run tests
   uv run pytest
   
   # Test CLI functionality
   rebuildr load-py examples/first.rebuildr.py
   
   # Test Bazel integration
   bazel test //bzl/...
   ```

4. **Commit your changes**: Use clear, descriptive commit messages
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

5. **Push and create PR**: Push your branch and create a pull request

### Coding Standards

- **Python**: Follow PEP 8 style guidelines
- **Documentation**: Add docstrings for new functions and classes
- **Tests**: Add tests for new functionality
- **Type hints**: Use type hints for function parameters and return values
- **Error handling**: Include proper error handling and meaningful error messages

### Commit Message Format

Use clear, descriptive commit messages:

```
Add feature: brief description

More detailed explanation of what was changed and why.
Include any breaking changes or important notes.
```

Examples:
- `Fix: resolve Docker daemon connection issue`
- `Add feature: support for multi-platform builds`
- `Update docs: improve Bazel integration guide`

## Testing Guidelines

### Unit Tests

- Test individual functions and classes
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies (Docker, file system)

### Integration Tests

- Test complete workflows
- Test CLI commands end-to-end
- Test Bazel rule integration
- Test with real Docker builds (when possible)

### Test Structure

```python
def test_descriptor_parsing():
    """Test that descriptors are parsed correctly."""
    # Arrange
    descriptor_content = "..."
    
    # Act
    result = parse_descriptor(descriptor_content)
    
    # Assert
    assert result.repository == "expected"
```

## Documentation

### Adding Documentation

- **API Reference**: Update `API_REFERENCE.md` for new classes/functions
- **Examples**: Add examples to `examples/` directory
- **Guides**: Update relevant guides for new features
- **README**: Update main README for significant changes

### Documentation Standards

- Use clear, concise language
- Include code examples
- Explain the "why" not just the "what"
- Keep examples up-to-date and working

## Release Process

### Version Bumping

- **Major**: Breaking changes
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes, backward compatible

### Release Checklist

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` (if exists)
3. Run full test suite
4. Update documentation
5. Create release tag
6. Build and test release artifacts

## Getting Help

### Questions and Discussion

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Pull Requests**: For code review and collaboration

### Code Review Process

1. **Automated checks**: CI will run tests and linting
2. **Manual review**: Maintainers will review your code
3. **Feedback**: Address any feedback or requested changes
4. **Merge**: Once approved, your changes will be merged

## Recognition

Contributors will be recognized in:
- **CONTRIBUTORS.md**: List of all contributors
- **Release notes**: Credit for significant contributions
- **Documentation**: Attribution for documentation improvements

Thank you for contributing to Rebuildr! Your efforts help make Docker image building more reproducible and efficient for everyone.
