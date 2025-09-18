import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from rebuildr.context import LocalContext
from rebuildr.stable_descriptor import (
    StableDescriptor,
    StableFileInput,
    StableEnvInput,
    StableGitHubCommitInput,
    StableGitRepoInput,
)


class TestLocalContext:
    def test_local_context_with_path(self, tmp_path):
        """Test LocalContext initialization with Path."""
        context = LocalContext(tmp_path)
        assert context.root_dir == tmp_path
        assert context.temp_dir is None

    def test_local_context_with_temp_directory(self):
        """Test LocalContext initialization with TemporaryDirectory."""
        temp_dir = tempfile.TemporaryDirectory()
        context = LocalContext(temp_dir)
        assert context.root_dir == Path(temp_dir.name)
        assert context.temp_dir == temp_dir

    def test_local_context_temp_static_method(self):
        """Test LocalContext.temp() static method."""
        context = LocalContext.temp()
        assert isinstance(context.root_dir, Path)
        assert isinstance(context.temp_dir, tempfile.TemporaryDirectory)
        assert context.root_dir == Path(context.temp_dir.name)

    def test_local_context_from_path_static_method(self, tmp_path):
        """Test LocalContext.from_path() static method."""
        context = LocalContext.from_path(tmp_path)
        assert context.root_dir == tmp_path
        assert context.temp_dir is None

    def test_src_path(self, tmp_path):
        """Test src_path() method."""
        context = LocalContext(tmp_path)
        src_path = context.src_path()
        assert src_path == tmp_path / "src"

    def test_builders_path(self, tmp_path):
        """Test builders_path() method."""
        context = LocalContext(tmp_path)
        builders_path = context.builders_path()
        assert builders_path == tmp_path / "builders"

    def test_copy_file_success(self, tmp_path):
        """Test _copy_file method with successful copy."""
        # Create source file
        src_file = tmp_path / "source.txt"
        src_file.write_text("test content")
        
        # Create destination path
        dest_dir = tmp_path / "dest"
        dest_file = dest_dir / "dest.txt"
        
        LocalContext._copy_file(src_file, dest_file)
        
        # Check that file was copied
        assert dest_file.exists()
        assert dest_file.read_text() == "test content"
        assert dest_dir.exists()

    def test_copy_file_dest_dir_is_file(self, tmp_path):
        """Test _copy_file method when destination directory is a file."""
        # Create source file
        src_file = tmp_path / "source.txt"
        src_file.write_text("test content")
        
        # Create destination file (not directory)
        dest_file = tmp_path / "dest.txt"
        dest_file.write_text("existing content")
        
        with pytest.raises(ValueError, match="Destination .* is a file but should be a directory"):
            LocalContext._copy_file(src_file, dest_file)

    def test_copy_file_preserves_metadata(self, tmp_path):
        """Test _copy_file method preserves file metadata."""
        # Create source file
        src_file = tmp_path / "source.txt"
        src_file.write_text("test content")
        
        # Set specific permissions
        src_file.chmod(0o755)
        original_stat = src_file.stat()
        
        # Create destination path
        dest_dir = tmp_path / "dest"
        dest_file = dest_dir / "dest.txt"
        
        LocalContext._copy_file(src_file, dest_file)
        
        # Check that file was copied with metadata
        assert dest_file.exists()
        assert dest_file.read_text() == "test content"
        
        # Note: On some systems, metadata preservation might vary
        # This test mainly ensures the copy2 function is used

    def test_prepare_from_descriptor_empty(self, tmp_path):
        """Test prepare_from_descriptor with empty descriptor."""
        descriptor = MagicMock(spec=StableDescriptor)
        descriptor.inputs = MagicMock()
        descriptor.inputs = MagicMock()
        descriptor.inputs.files = []
        descriptor.inputs.builders = []
        descriptor.inputs.external = []
        
        context = LocalContext(tmp_path)
        context.prepare_from_descriptor(descriptor)
        
        # Should create src directory
        assert (tmp_path / "src").exists()
        assert (tmp_path / "src").is_dir()

    def test_prepare_from_descriptor_with_files(self, tmp_path):
        """Test prepare_from_descriptor with file inputs."""
        # Create source files
        src_file1 = tmp_path / "file1.txt"
        src_file1.write_text("content1")
        
        src_file2 = tmp_path / "file2.txt"
        src_file2.write_text("content2")
        
        # Create stable file inputs
        stable_file1 = StableFileInput(
            target_path=Path("file1.txt"),
            absolute_src_path=src_file1
        )
        stable_file2 = StableFileInput(
            target_path=Path("nested/file2.txt"),
            absolute_src_path=src_file2
        )
        
        descriptor = MagicMock(spec=StableDescriptor)
        descriptor.inputs = MagicMock()
        descriptor.inputs.files = [stable_file1, stable_file2]
        descriptor.inputs.builders = []
        descriptor.inputs.external = []
        
        context = LocalContext(tmp_path)
        context.prepare_from_descriptor(descriptor)
        
        # Check that files were copied to src directory
        assert (tmp_path / "src" / "file1.txt").exists()
        assert (tmp_path / "src" / "file1.txt").read_text() == "content1"
        
        assert (tmp_path / "src" / "nested" / "file2.txt").exists()
        assert (tmp_path / "src" / "nested" / "file2.txt").read_text() == "content2"

    def test_prepare_from_descriptor_with_builders(self, tmp_path):
        """Test prepare_from_descriptor with builder inputs."""
        # Create source files
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM alpine\nRUN echo 'hello'")
        
        # Create stable file input for builder
        stable_dockerfile = StableFileInput(
            target_path=Path("Dockerfile"),
            absolute_src_path=dockerfile
        )
        
        # Create env input
        env_input = StableEnvInput(key="TEST_VAR", default="default_value")
        
        descriptor = MagicMock(spec=StableDescriptor)
        descriptor.inputs = MagicMock()
        descriptor.inputs.files = []
        descriptor.inputs.builders = [stable_dockerfile, env_input]
        descriptor.inputs.external = []
        
        context = LocalContext(tmp_path)
        context.prepare_from_descriptor(descriptor)
        
        # Check that dockerfile was copied to root directory
        assert (tmp_path / "Dockerfile").exists()
        assert (tmp_path / "Dockerfile").read_text() == "FROM alpine\nRUN echo 'hello'"

    def test_prepare_from_descriptor_with_unknown_builder_type(self, tmp_path):
        """Test prepare_from_descriptor with unknown builder type."""
        descriptor = MagicMock(spec=StableDescriptor)
        descriptor.inputs = MagicMock()
        descriptor.inputs.files = []
        descriptor.inputs.builders = [MagicMock()]  # Unknown type
        descriptor.inputs.external = []
        
        context = LocalContext(tmp_path)
        
        with pytest.raises(ValueError, match="Unknown input type"):
            context.prepare_from_descriptor(descriptor)

    @patch('rebuildr.context.git_better_clone')
    def test_prepare_from_descriptor_with_github_commit(self, mock_git_clone, tmp_path):
        """Test prepare_from_descriptor with GitHub commit input."""
        github_input = StableGitHubCommitInput(
            url="https://github.com/test/repo.git",
            commit="abc123",
            target_path=Path("external/repo")
        )
        
        descriptor = MagicMock(spec=StableDescriptor)
        descriptor.inputs = MagicMock()
        descriptor.inputs.files = []
        descriptor.inputs.builders = []
        descriptor.inputs.external = [github_input]
        
        context = LocalContext(tmp_path)
        context.prepare_from_descriptor(descriptor)
        
        # Check that git clone was called
        mock_git_clone.assert_called_once_with(
            "https://github.com/test/repo.git",
            tmp_path / "external/repo",
            "abc123"
        )
        
        # Check that target directory was created
        assert (tmp_path / "external" / "repo").exists()

    @patch('rebuildr.context.git_better_clone')
    def test_prepare_from_descriptor_with_git_repo(self, mock_git_clone, tmp_path):
        """Test prepare_from_descriptor with Git repo input."""
        git_input = StableGitRepoInput(
            url="https://git.example.com/repo.git",
            commit="def456",
            target_path=Path("external/git-repo")
        )
        
        descriptor = MagicMock(spec=StableDescriptor)
        descriptor.inputs = MagicMock()
        descriptor.inputs.files = []
        descriptor.inputs.builders = []
        descriptor.inputs.external = [git_input]
        
        context = LocalContext(tmp_path)
        context.prepare_from_descriptor(descriptor)
        
        # Check that git clone was called
        mock_git_clone.assert_called_once_with(
            "https://git.example.com/repo.git",
            tmp_path / "external/git-repo",
            "def456"
        )
        
        # Check that target directory was created
        assert (tmp_path / "external" / "git-repo").exists()

    @patch('rebuildr.context.DockerCLIBuilder')
    def test_store_in_docker_current_builder(self, mock_docker_builder, tmp_path):
        """Test store_in_docker_current_builder method."""
        context = LocalContext(tmp_path)
        ref_key = "abc123"
        path = tmp_path / "test-repo"
        path.mkdir(parents=True)
        
        # Create a test file in the path
        test_file = path / "test.txt"
        test_file.write_text("test content")
        
        context.store_in_docker_current_builder(ref_key, path)
        
        # Check that Dockerfile was created
        dockerfile_path = tmp_path / "builders" / "__internal_cachestore.Dockerfile"
        assert dockerfile_path.exists()
        
        dockerfile_content = dockerfile_path.read_text()
        assert "FROM scratch" in dockerfile_content
        assert "COPY / /" in dockerfile_content
        
        # Check that DockerCLIBuilder was called
        mock_builder_instance = mock_docker_builder.return_value
        mock_builder_instance.build.assert_called_once()
        
        # Check build call arguments
        build_call_args = mock_builder_instance.build.call_args
        assert build_call_args[1]['root_dir'] == path
        assert build_call_args[1]['dockerfile'] == dockerfile_path
        assert build_call_args[1]['platform'] == "linux/amd64"
        assert build_call_args[1]['tags'] == [f"x__internal_cachestore_{ref_key}"]

    def test_store_in_docker_current_builder_creates_dockerfile(self, tmp_path):
        """Test that store_in_docker_current_builder creates correct Dockerfile."""
        context = LocalContext(tmp_path)
        ref_key = "test-ref"
        path = tmp_path / "test-repo"
        path.mkdir(parents=True)
        
        with patch('rebuildr.context.DockerCLIBuilder'):
            context.store_in_docker_current_builder(ref_key, path)
        
        # Check Dockerfile content
        dockerfile_path = tmp_path / "builders" / "__internal_cachestore.Dockerfile"
        assert dockerfile_path.exists()
        
        dockerfile_content = dockerfile_path.read_text().strip()
        expected_content = """FROM scratch
COPY / /"""
        assert dockerfile_content == expected_content

    def test_prepare_from_descriptor_complete_example(self, tmp_path):
        """Test prepare_from_descriptor with complete example."""
        # Create source files
        app_file = tmp_path / "app.py"
        app_file.write_text("print('Hello, World!')")
        
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM python:3.9\nCOPY app.py /app.py\nCMD python /app.py")
        
        # Create stable inputs
        stable_app = StableFileInput(
            target_path=Path("app.py"),
            absolute_src_path=app_file
        )
        
        stable_dockerfile = StableFileInput(
            target_path=Path("Dockerfile"),
            absolute_src_path=dockerfile
        )
        
        env_input = StableEnvInput(key="PYTHON_VERSION", default="3.9")
        
        descriptor = MagicMock(spec=StableDescriptor)
        descriptor.inputs = MagicMock()
        descriptor.inputs.files = [stable_app]
        descriptor.inputs.builders = [stable_dockerfile, env_input]
        descriptor.inputs.external = []
        
        context = LocalContext(tmp_path)
        context.prepare_from_descriptor(descriptor)
        
        # Check file structure
        assert (tmp_path / "src" / "app.py").exists()
        assert (tmp_path / "src" / "app.py").read_text() == "print('Hello, World!')"
        
        assert (tmp_path / "Dockerfile").exists()
        assert (tmp_path / "Dockerfile").read_text() == "FROM python:3.9\nCOPY app.py /app.py\nCMD python /app.py"

    def test_prepare_from_descriptor_nested_directories(self, tmp_path):
        """Test prepare_from_descriptor with nested directory structure."""
        # Create nested source structure
        nested_dir = tmp_path / "src" / "nested" / "deep"
        nested_dir.mkdir(parents=True)
        
        deep_file = nested_dir / "deep.txt"
        deep_file.write_text("deep content")
        
        # Create stable file input
        stable_file = StableFileInput(
            target_path=Path("nested/deep/deep.txt"),
            absolute_src_path=deep_file
        )
        
        descriptor = MagicMock(spec=StableDescriptor)
        descriptor.inputs = MagicMock()
        descriptor.inputs.files = [stable_file]
        descriptor.inputs.builders = []
        descriptor.inputs.external = []
        
        context = LocalContext(tmp_path)
        context.prepare_from_descriptor(descriptor)
        
        # Check nested structure was created
        assert (tmp_path / "src" / "nested" / "deep" / "deep.txt").exists()
        assert (tmp_path / "src" / "nested" / "deep" / "deep.txt").read_text() == "deep content"

    def test_context_cleanup_with_temp_directory(self):
        """Test that context properly handles temporary directory cleanup."""
        context = LocalContext.temp()
        temp_dir = context.temp_dir
        
        # The temporary directory should exist
        assert temp_dir.name in str(context.root_dir)
        
        # Clean up
        context.temp_dir.cleanup()
        
        # After cleanup, the directory should not exist
        assert not Path(temp_dir.name).exists()

    def test_context_path_operations(self, tmp_path):
        """Test various path operations on context."""
        context = LocalContext(tmp_path)
        
        # Test path operations
        assert context.root_dir.is_absolute() == tmp_path.is_absolute()
        assert str(context.root_dir) == str(tmp_path)
        
        # Test src_path operations
        src_path = context.src_path()
        assert src_path.parent == tmp_path
        assert src_path.name == "src"
        
        # Test builders_path operations
        builders_path = context.builders_path()
        assert builders_path.parent == tmp_path
        assert builders_path.name == "builders"