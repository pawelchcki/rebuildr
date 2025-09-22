# Troubleshooting Guide

This guide helps you resolve common issues when using Rebuildr.

## Common Issues

### CLI Issues

#### "Cannot load descriptor from path"

**Error:**
```
ImportError: Cannot load descriptor from path: /path/to/file.rebuildr.py
```

**Causes:**
- File doesn't exist
- File is not readable
- Invalid Python syntax in descriptor file

**Solutions:**
1. Check file exists: `ls -la /path/to/file.rebuildr.py`
2. Verify file permissions: `chmod 644 /path/to/file.rebuildr.py`
3. Test Python syntax: `python -m py_compile /path/to/file.rebuildr.py`

#### "Descriptor missing 'image' variable"

**Error:**
```
AttributeError: module 'rebuildr.external.desc' has no attribute 'image'
```

**Causes:**
- Descriptor file doesn't export `image` variable
- Variable name is misspelled
- Descriptor object creation failed

**Solutions:**
1. Ensure your `.rebuildr.py` file ends with:
   ```python
   image = Descriptor(...)
   ```
2. Check for typos in variable name
3. Verify all imports are correct

#### "File not found" errors

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'src/'
```

**Causes:**
- Referenced files don't exist
- Incorrect relative paths
- Missing dependencies

**Solutions:**
1. Verify file paths exist relative to descriptor location
2. Use absolute paths if needed
3. Check `REBUILDR_OVERRIDE_ROOT_DIR` environment variable

### Docker Issues

#### "Docker daemon not running"

**Error:**
```
docker.errors.DockerException: Error while fetching server API version
```

**Solutions:**
1. Start Docker daemon: `sudo systemctl start docker`
2. Add user to docker group: `sudo usermod -aG docker $USER`
3. Restart shell session

#### "Permission denied" when building

**Error:**
```
permission denied while trying to connect to the Docker daemon socket
```

**Solutions:**
1. Add user to docker group: `sudo usermod -aG docker $USER`
2. Log out and log back in
3. Test with: `docker run hello-world`

#### "No space left on device"

**Error:**
```
no space left on device
```

**Solutions:**
1. Clean up Docker: `docker system prune -a`
2. Remove unused images: `docker image prune -a`
3. Check disk space: `df -h`

### Bazel Issues

#### "Rule not found"

**Error:**
```
ERROR: /path/to/BUILD:1:1: no such target '//path/to:target': target 'target' not declared in package 'path/to'
```

**Solutions:**
1. Check rule name spelling
2. Verify rule is loaded: `load("@rebuildr//:rebuildr.bzl", "rebuildr_image")`
3. Ensure target exists in BUILD file

#### "File not found in srcs"

**Error:**
```
ERROR: /path/to/BUILD:1:1: //path/to:target: missing input file 'src/file.py'
```

**Solutions:**
1. Check file exists in `srcs` list
2. Use `glob()` for multiple files: `glob(["src/**/*"])`
3. Verify file paths are correct

#### "Descriptor parsing failed"

**Error:**
```
ERROR: /path/to/BUILD:1:1: //path/to:target: Python descriptor parsing failed
```

**Solutions:**
1. Test descriptor manually: `rebuildr load-py descriptor.rebuildr.py`
2. Check Python syntax
3. Verify all imports are available

### Build Issues

#### "Content hash mismatch"

**Symptoms:**
- Images rebuild unnecessarily
- Cache not working properly
- Inconsistent builds

**Causes:**
- Timestamps in files
- Environment variables changing
- External dependencies updating

**Solutions:**
1. Use `FileInput` instead of string paths for better control
2. Check environment variables in `builders`
3. Pin external dependencies to specific commits

#### "Platform-specific build failures"

**Error:**
```
failed to solve: platform linux/arm64 not supported
```

**Solutions:**
1. Check Docker supports the platform: `docker buildx ls`
2. Use supported platforms: `linux/amd64`, `linux/arm64`
3. Enable buildx: `docker buildx create --use`

#### "Registry authentication failed"

**Error:**
```
denied: requested access to the resource is denied
```

**Solutions:**
1. Login to registry: `docker login registry.example.com`
2. Check credentials are correct
3. Verify image repository permissions

## Debugging Commands

### CLI Debugging

```bash
# Test descriptor parsing
rebuildr load-py myapp.rebuildr.py

# Verbose output
rebuildr load-py myapp.rebuildr.py --verbose

# Check environment variables
env | grep REBUILDR
env | grep DOCKER
```

### Bazel Debugging

```bash
# Verbose build output
bazel build //path/to:target --verbose_failures

# Check file dependencies
bazel query --output=graph //path/to:target

# Inspect working directory
bazel build //path/to:target
ls -la bazel-bin/path/to/target.work_dir/

# Check stable metadata
cat bazel-bin/path/to/target.stable
```

### Docker Debugging

```bash
# Check Docker daemon status
docker info

# List available platforms
docker buildx ls

# Test Docker build
docker build -t test .

# Check image layers
docker history myimage:latest
```

## Environment Variables

### Rebuildr Variables

- `REBUILDR_OVERRIDE_ROOT_DIR`: Override root directory for file resolution
- `DOCKER_QUIET`: Reduce Docker build output noise

### Docker Variables

- `DOCKER_BUILDKIT`: Enable BuildKit (set to "1")
- `DOCKER_CONFIG`: Docker configuration directory
- `DOCKER_HOST`: Docker daemon socket

## Performance Issues

### Slow Builds

**Causes:**
- Large file inputs
- Network dependencies
- Inefficient Dockerfile

**Solutions:**
1. Use `.dockerignore` to exclude unnecessary files
2. Minimize `files` inputs to only necessary files
3. Use multi-stage Dockerfiles
4. Leverage Docker layer caching

### Memory Issues

**Symptoms:**
- Build process killed
- Out of memory errors
- System becomes unresponsive

**Solutions:**
1. Increase system memory
2. Use smaller base images
3. Build one image at a time
4. Clean up Docker resources regularly

## Getting Help

### Log Collection

When reporting issues, include:

1. **Descriptor file**: The `.rebuildr.py` file causing issues
2. **Error output**: Complete error message and stack trace
3. **Environment info**:
   ```bash
   rebuildr --version
   docker --version
   bazel --version
   python --version
   ```
4. **System info**:
   ```bash
   uname -a
   df -h
   free -h
   ```

### Common Log Locations

- **Docker logs**: `journalctl -u docker.service`
- **Bazel logs**: `~/.cache/bazel/_bazel_*/command.log`
- **System logs**: `/var/log/syslog` or `journalctl`

### Community Support

- **GitHub Issues**: Report bugs and feature requests
- **Discussions**: Ask questions and share solutions
- **Documentation**: Check existing guides and examples

## Prevention

### Best Practices

1. **Use version control** for all descriptor files
2. **Pin external dependencies** to specific commits
3. **Test descriptors** before committing
4. **Use consistent environments** across development and CI
5. **Monitor build times** and optimize as needed

### Regular Maintenance

1. **Clean Docker resources**: `docker system prune`
2. **Update base images** regularly
3. **Review and optimize** descriptor files
4. **Monitor disk space** usage
5. **Keep tools updated** to latest versions

This troubleshooting guide should help you resolve most common issues. If you encounter problems not covered here, please open an issue with detailed information about your setup and the error you're experiencing.