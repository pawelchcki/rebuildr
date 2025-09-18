import pytest
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from rebuildr.build import DockerCLIBuilder, _CommandBuilder


class TestCommandBuilder:
    def test_command_builder_initialization(self):
        """Test CommandBuilder initialization."""
        builder = _CommandBuilder()
        assert builder._args == ["docker", "buildx", "build"]

    def test_command_builder_add_arg_with_value(self):
        """Test adding argument with value."""
        builder = _CommandBuilder()
        builder.add_arg("--file", "Dockerfile")
        
        assert "--file" in builder._args
        assert "Dockerfile" in builder._args
        assert builder._args.index("--file") + 1 == builder._args.index("Dockerfile")

    def test_command_builder_add_arg_without_value(self):
        """Test adding argument without value (should not add)."""
        builder = _CommandBuilder()
        builder.add_arg("--file", None)
        
        assert "--file" not in builder._args

    def test_command_builder_add_flag_true(self):
        """Test adding flag when True."""
        builder = _CommandBuilder()
        builder.add_flag("--no-cache", True)
        
        assert "--no-cache" in builder._args

    def test_command_builder_add_flag_false(self):
        """Test adding flag when False."""
        builder = _CommandBuilder()
        builder.add_flag("--no-cache", False)
        
        assert "--no-cache" not in builder._args

    def test_command_builder_add_params(self):
        """Test adding build parameters."""
        builder = _CommandBuilder()
        params = {"ARG1": "value1", "ARG2": "value2"}
        builder.add_params("--build-arg", params)
        
        assert "--build-arg" in builder._args
        assert "ARG1=value1" in builder._args
        assert "ARG2=value2" in builder._args

    def test_command_builder_add_params_empty(self):
        """Test adding empty parameters (should not add)."""
        builder = _CommandBuilder()
        builder.add_params("--build-arg", {})
        
        assert "--build-arg" not in builder._args

    def test_command_builder_add_list(self):
        """Test adding list of values."""
        builder = _CommandBuilder()
        values = ["cache1", "cache2"]
        builder.add_list("--cache-from", values)
        
        assert "--cache-from" in builder._args
        assert "cache1" in builder._args
        assert "cache2" in builder._args

    def test_command_builder_add_list_empty(self):
        """Test adding empty list (should not add)."""
        builder = _CommandBuilder()
        builder.add_list("--cache-from", [])
        
        assert "--cache-from" not in builder._args

    def test_command_builder_build(self):
        """Test building final command."""
        builder = _CommandBuilder()
        builder.add_arg("--file", "Dockerfile")
        builder.add_flag("--no-cache", True)
        
        args = ["/path/to/context"]
        result = builder.build(args)
        
        expected = ["docker", "buildx", "build", "--file", "Dockerfile", "--no-cache"] + args
        assert result == expected

    def test_command_builder_build_with_string_conversion(self):
        """Test that build converts all arguments to strings."""
        builder = _CommandBuilder()
        builder.add_arg("--file", Path("Dockerfile"))
        
        args = [Path("/path/to/context")]
        result = builder.build(args)
        
        # All elements should be strings
        assert all(isinstance(arg, str) for arg in result)


class TestDockerCLIBuilder:
    def test_docker_cli_builder_initialization_default(self):
        """Test DockerCLIBuilder initialization with default settings."""
        builder = DockerCLIBuilder()
        assert builder._progress == "auto"
        assert builder.quiet is False

    @patch.dict(os.environ, {"DOCKER_QUIET": "1"})
    def test_docker_cli_builder_initialization_quiet(self):
        """Test DockerCLIBuilder initialization with quiet mode."""
        builder = DockerCLIBuilder()
        assert builder._progress == "auto"
        assert builder.quiet is True

    @patch('rebuildr.build.subprocess.Popen')
    @patch('rebuildr.build.tempfile.mkstemp')
    def test_docker_cli_builder_build_success(self, mock_mkstemp, mock_popen):
        """Test successful docker build."""
        mock_mkstemp.return_value = (1, "/tmp/iidfile")
        
        # Mock successful subprocess
        mock_process = MagicMock()
        mock_process.wait.return_value = 0
        mock_popen.return_value.__enter__.return_value = mock_process
        
        # Mock iidfile content
        with patch('builtins.open', mock_open(read_data="sha256:abc123def456")):
            builder = DockerCLIBuilder()
            result = builder.build(
                root_dir=Path("/tmp"),
                dockerfile=Path("Dockerfile"),
                tags=["test:latest"],
                buildargs={"ARG1": "value1"}
            )
        
        assert result == "abc123def456"
        mock_popen.assert_called_once()

    @patch('rebuildr.build.subprocess.Popen')
    @patch('rebuildr.build.tempfile.mkstemp')
    def test_docker_cli_builder_build_quiet_mode(self, mock_mkstemp, mock_popen):
        """Test docker build in quiet mode."""
        mock_mkstemp.return_value = (1, "/tmp/iidfile")
        
        # Mock successful subprocess
        mock_process = MagicMock()
        mock_process.wait.return_value = 0
        mock_process.communicate.return_value = ("stdout", "stderr")
        mock_popen.return_value.__enter__.return_value = mock_process
        
        # Mock iidfile content
        with patch('builtins.open', mock_open(read_data="sha256:abc123def456")):
            builder = DockerCLIBuilder()
            builder.quiet = True
            result = builder.build(
                root_dir=Path("/tmp"),
                dockerfile=Path("Dockerfile"),
                tags=["test:latest"]
            )
        
        assert result == "abc123def456"
        mock_popen.assert_called_once()

    @patch('rebuildr.build.subprocess.Popen')
    @patch('rebuildr.build.tempfile.mkstemp')
    def test_docker_cli_builder_build_failure(self, mock_mkstemp, mock_popen):
        """Test docker build failure."""
        mock_mkstemp.return_value = (1, "/tmp/iidfile")
        
        # Mock failed subprocess
        mock_process = MagicMock()
        mock_process.wait.return_value = 1
        mock_popen.return_value.__enter__.return_value = mock_process
        
        builder = DockerCLIBuilder()
        
        with pytest.raises(Exception, match="Builder exited with code 1"):
            builder.build(
                root_dir=Path("/tmp"),
                dockerfile=Path("Dockerfile"),
                tags=["test:latest"]
            )

    @patch('rebuildr.build.subprocess.Popen')
    @patch('rebuildr.build.tempfile.mkstemp')
    def test_docker_cli_builder_build_quiet_mode_failure(self, mock_mkstemp, mock_popen):
        """Test docker build failure in quiet mode."""
        mock_mkstemp.return_value = (1, "/tmp/iidfile")
        
        # Mock failed subprocess
        mock_process = MagicMock()
        mock_process.wait.return_value = 1
        mock_process.communicate.return_value = ("stdout", "stderr")
        mock_popen.return_value.__enter__.return_value = mock_process
        
        builder = DockerCLIBuilder()
        builder.quiet = True
        
        # In quiet mode, failure should not raise exception but print error
        with patch('builtins.print') as mock_print:
            with patch('builtins.open', mock_open(read_data="sha256:abc123def456")):
                builder.build(
                    root_dir=Path("/tmp"),
                    dockerfile=Path("Dockerfile"),
                    tags=["test:latest"]
                )
        
        mock_print.assert_called()

    @patch('rebuildr.build.subprocess.Popen')
    @patch('rebuildr.build.tempfile.mkstemp')
    def test_docker_cli_builder_build_invalid_iidfile(self, mock_mkstemp, mock_popen):
        """Test docker build with invalid iidfile content."""
        mock_mkstemp.return_value = (1, "/tmp/iidfile")
        
        # Mock successful subprocess
        mock_process = MagicMock()
        mock_process.wait.return_value = 0
        mock_popen.return_value.__enter__.return_value = mock_process
        
        # Mock invalid iidfile content
        with patch('builtins.open', mock_open(read_data="invalid_content")):
            builder = DockerCLIBuilder()
            
            with pytest.raises(Exception, match="stop"):
                builder.build(
                    root_dir=Path("/tmp"),
                    dockerfile=Path("Dockerfile"),
                    tags=["test:latest"]
                )

    @patch('rebuildr.build.subprocess.Popen')
    @patch('rebuildr.build.tempfile.mkstemp')
    def test_docker_cli_builder_build_with_all_parameters(self, mock_mkstemp, mock_popen):
        """Test docker build with all parameters."""
        mock_mkstemp.return_value = (1, "/tmp/iidfile")
        
        # Mock successful subprocess
        mock_process = MagicMock()
        mock_process.wait.return_value = 0
        mock_popen.return_value.__enter__.return_value = mock_process
        
        # Mock iidfile content
        with patch('builtins.open', mock_open(read_data="sha256:abc123def456")):
            builder = DockerCLIBuilder()
            result = builder.build(
                root_dir=Path("/tmp"),
                dockerfile=Path("Dockerfile"),
                tags=["test:latest", "test:v1.0"],
                nocache=True,
                pull=True,
                forcerm=True,
                container_limits={"memory": "1g"},
                buildargs={"ARG1": "value1", "ARG2": "value2"},
                cache_from=["cache1", "cache2"],
                platform="linux/amd64",
                target="production",
                build_context=["ctx1=src1", "ctx2=src2"]
            )
        
        assert result == "abc123def456"
        mock_popen.assert_called_once()

    @patch('rebuildr.build.subprocess.Popen')
    @patch('rebuildr.build.tempfile.mkstemp')
    def test_docker_cli_builder_build_relative_dockerfile(self, mock_mkstemp, mock_popen):
        """Test docker build with relative dockerfile path."""
        mock_mkstemp.return_value = (1, "/tmp/iidfile")
        
        # Mock successful subprocess
        mock_process = MagicMock()
        mock_process.wait.return_value = 0
        mock_popen.return_value.__enter__.return_value = mock_process
        
        # Mock iidfile content
        with patch('builtins.open', mock_open(read_data="sha256:abc123def456")):
            builder = DockerCLIBuilder()
            result = builder.build(
                root_dir=Path("/tmp"),
                dockerfile=Path("custom.Dockerfile"),
                tags=["test:latest"]
            )
        
        assert result == "abc123def456"
        mock_popen.assert_called_once()

    @patch('rebuildr.build.subprocess.Popen')
    @patch('rebuildr.build.tempfile.mkstemp')
    def test_docker_cli_builder_build_no_dockerfile(self, mock_mkstemp, mock_popen):
        """Test docker build without specifying dockerfile."""
        mock_mkstemp.return_value = (1, "/tmp/iidfile")
        
        # Mock successful subprocess
        mock_process = MagicMock()
        mock_process.wait.return_value = 0
        mock_popen.return_value.__enter__.return_value = mock_process
        
        # Mock iidfile content
        with patch('builtins.open', mock_open(read_data="sha256:abc123def456")):
            builder = DockerCLIBuilder()
            result = builder.build(
                root_dir=Path("/tmp"),
                dockerfile=None,
                tags=["test:latest"]
            )
        
        assert result == "abc123def456"
        mock_popen.assert_called_once()

    @patch('rebuildr.build.subprocess.Popen')
    @patch('rebuildr.build.tempfile.mkstemp')
    def test_docker_cli_builder_build_duplicate_tags(self, mock_mkstemp, mock_popen):
        """Test docker build with duplicate tags (should be deduplicated)."""
        mock_mkstemp.return_value = (1, "/tmp/iidfile")
        
        # Mock successful subprocess
        mock_process = MagicMock()
        mock_process.wait.return_value = 0
        mock_popen.return_value.__enter__.return_value = mock_process
        
        # Mock iidfile content
        with patch('builtins.open', mock_open(read_data="sha256:abc123def456")):
            builder = DockerCLIBuilder()
            result = builder.build(
                root_dir=Path("/tmp"),
                dockerfile=Path("Dockerfile"),
                tags=["test:latest", "test:latest", "test:v1.0"]  # Duplicate tag
            )
        
        assert result == "abc123def456"
        mock_popen.assert_called_once()

    @patch('rebuildr.build.subprocess.Popen')
    @patch('rebuildr.build.tempfile.mkstemp')
    def test_docker_cli_builder_build_load_flag(self, mock_mkstemp, mock_popen):
        """Test docker build includes --load flag."""
        mock_mkstemp.return_value = (1, "/tmp/iidfile")
        
        # Mock successful subprocess
        mock_process = MagicMock()
        mock_process.wait.return_value = 0
        mock_popen.return_value.__enter__.return_value = mock_process
        
        # Mock iidfile content
        with patch('builtins.open', mock_open(read_data="sha256:abc123def456")):
            builder = DockerCLIBuilder()
            result = builder.build(
                root_dir=Path("/tmp"),
                dockerfile=Path("Dockerfile"),
                tags=["test:latest"]
            )
        
        # Check that --load flag is included in the command
        call_args = mock_popen.call_args[0][0]
        assert "--load" in call_args
        
        assert result == "abc123def456"

    @patch('rebuildr.build.subprocess.Popen')
    @patch('rebuildr.build.tempfile.mkstemp')
    def test_docker_cli_builder_build_iidfile_parameter(self, mock_mkstemp, mock_popen):
        """Test docker build includes --iidfile parameter."""
        mock_mkstemp.return_value = (1, "/tmp/iidfile")
        
        # Mock successful subprocess
        mock_process = MagicMock()
        mock_process.wait.return_value = 0
        mock_popen.return_value.__enter__.return_value = mock_process
        
        # Mock iidfile content
        with patch('builtins.open', mock_open(read_data="sha256:abc123def456")):
            builder = DockerCLIBuilder()
            result = builder.build(
                root_dir=Path("/tmp"),
                dockerfile=Path("Dockerfile"),
                tags=["test:latest"]
            )
        
        # Check that --iidfile parameter is included
        call_args = mock_popen.call_args[0][0]
        assert "--iidfile" in call_args
        assert "/tmp/iidfile" in call_args
        
        assert result == "abc123def456"

    @patch('rebuildr.build.subprocess.Popen')
    @patch('rebuildr.build.tempfile.mkstemp')
    def test_docker_cli_builder_build_context_path(self, mock_mkstemp, mock_popen):
        """Test docker build includes context path as last argument."""
        mock_mkstemp.return_value = (1, "/tmp/iidfile")
        
        # Mock successful subprocess
        mock_process = MagicMock()
        mock_process.wait.return_value = 0
        mock_popen.return_value.__enter__.return_value = mock_process
        
        # Mock iidfile content
        with patch('builtins.open', mock_open(read_data="sha256:abc123def456")):
            builder = DockerCLIBuilder()
            result = builder.build(
                root_dir=Path("/tmp/context"),
                dockerfile=Path("Dockerfile"),
                tags=["test:latest"]
            )
        
        # Check that context path is the last argument
        call_args = mock_popen.call_args[0][0]
        assert call_args[-1] == "/tmp/context"
        
        assert result == "abc123def456"