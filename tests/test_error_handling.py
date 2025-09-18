import pytest
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from rebuildr.cli import (
    load_py_desc,
    build_docker,
    build_tar,
    parse_cli_parse_py,
    parse_build_args,
)
from rebuildr.context import LocalContext
from rebuildr.containers.docker import (
    docker_bin,
    docker_image_exists_locally,
    docker_image_exists_in_registry,
    docker_pull_image,
    docker_push_image,
)
from rebuildr.build import DockerCLIBuilder
from rebuildr.tools.git import git_command, git_ls_remote
from rebuildr.stable_descriptor import (
    StableDescriptor,
    StableFileInput,
    StableEnvironment,
)
from rebuildr.descriptor import (
    GitHubCommitInput,
    GitRepoInput,
    Descriptor,
    Inputs,
    ImageTarget,
)


class TestCLIErrorHandling:
    def test_load_py_desc_file_not_found(self):
        """Test load_py_desc with non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_py_desc("nonexistent.rebuildr.py")

    def test_load_py_desc_invalid_python_syntax(self, tmp_path):
        """Test load_py_desc with invalid Python syntax."""
        rebuildr_file = tmp_path / "invalid.rebuildr.py"
        rebuildr_file.write_text("invalid python syntax !!!")
        
        with pytest.raises(SyntaxError):
            load_py_desc(rebuildr_file)

    def test_load_py_desc_missing_image_variable(self, tmp_path):
        """Test load_py_desc with missing image variable."""
        rebuildr_file = tmp_path / "missing_image.rebuildr.py"
        rebuildr_file.write_text("""
# Missing image variable
some_other_variable = "test"
""")
        
        with pytest.raises(NameError):
            load_py_desc(rebuildr_file)

    def test_load_py_desc_invalid_descriptor_type(self, tmp_path):
        """Test load_py_desc with invalid descriptor type."""
        rebuildr_file = tmp_path / "invalid_type.rebuildr.py"
        rebuildr_file.write_text("""
# image should be a Descriptor, not a string
image = "invalid descriptor"
""")
        
        with pytest.raises(AttributeError):
            load_py_desc(rebuildr_file)

    def test_build_docker_no_targets(self, tmp_path):
        """Test build_docker with descriptor having no targets."""
        rebuildr_file = tmp_path / "no_targets.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs

image = Descriptor(inputs=Inputs())
""")
        
        with pytest.raises(ValueError, match="Only one target is supported"):
            build_docker(str(rebuildr_file), {})

    def test_build_docker_multiple_targets(self, tmp_path):
        """Test build_docker with descriptor having multiple targets."""
        rebuildr_file = tmp_path / "multiple_targets.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget

image = Descriptor(
    inputs=Inputs(),
    targets=[
        ImageTarget(repository="test1", tag="latest"),
        ImageTarget(repository="test2", tag="latest")
    ]
)
""")
        
        (tmp_path / "Dockerfile").write_text("FROM alpine")
        
        with pytest.raises(ValueError, match="Only one target is supported"):
            build_docker(str(rebuildr_file), {})

    def test_build_docker_no_tags(self, tmp_path):
        """Test build_docker with target having no tags."""
        rebuildr_file = tmp_path / "no_tags.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget

image = Descriptor(
    inputs=Inputs(),
    targets=[
        ImageTarget(
            repository="test-repo",
            also_tag_with_content_id=False
        )
    ]
)
""")
        
        (tmp_path / "Dockerfile").write_text("FROM alpine")
        
        with pytest.raises(ValueError, match="No tags specified"):
            build_docker(str(rebuildr_file), {})

    def test_build_tar_missing_file(self, tmp_path):
        """Test build_tar with missing file."""
        rebuildr_file = tmp_path / "missing_file.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs, FileInput

image = Descriptor(
    inputs=Inputs(
        files=[
            FileInput(path="nonexistent.txt", target_path="nonexistent.txt")
        ]
    )
)
""")
        
        output_tar = tmp_path / "output.tar"
        
        with pytest.raises(FileNotFoundError):
            build_tar(str(rebuildr_file), str(output_tar))

    def test_parse_cli_parse_py_no_file_path(self, capsys):
        """Test parse_cli_parse_py with no file path."""
        parse_cli_parse_py([])
        
        captured = capsys.readouterr()
        assert "Path to rebuildr file is required" in captured.out

    def test_parse_cli_parse_py_bazel_stable_metadata_insufficient_args(self, capsys):
        """Test parse_cli_parse_py with insufficient args for bazel-stable-metadata."""
        args = ["test.rebuildr.py", "bazel-stable-metadata", "metadata.json"]
        parse_cli_parse_py(args)
        
        captured = capsys.readouterr()
        assert "Stable metadata files must be specified" in captured.out

    def test_parse_cli_parse_py_build_tar_insufficient_args(self, capsys):
        """Test parse_cli_parse_py with insufficient args for build-tar."""
        args = ["test.rebuildr.py", "build-tar"]
        parse_cli_parse_py(args)
        
        captured = capsys.readouterr()
        assert "Tar path is required" in captured.out

    def test_parse_build_args_invalid_format(self):
        """Test parse_build_args with invalid format."""
        args = ["invalid_arg_without_equals"]
        result = parse_build_args(args)
        
        # Should not raise error, just ignore invalid args
        assert result == {}


class TestContextErrorHandling:
    def test_local_context_copy_file_dest_is_file(self, tmp_path):
        """Test LocalContext._copy_file when destination is a file."""
        src_file = tmp_path / "source.txt"
        src_file.write_text("source content")
        
        dest_file = tmp_path / "dest.txt"
        dest_file.write_text("existing content")
        
        with pytest.raises(ValueError, match="Destination .* is a file but should be a directory"):
            LocalContext._copy_file(src_file, dest_file)

    def test_local_context_prepare_from_descriptor_unknown_builder_type(self, tmp_path):
        """Test LocalContext.prepare_from_descriptor with unknown builder type."""
        descriptor = MagicMock()
        descriptor.inputs.files = []
        descriptor.inputs.builders = [MagicMock()]  # Unknown type
        descriptor.inputs.external = []
        
        context = LocalContext(tmp_path)
        
        with pytest.raises(ValueError, match="Unknown input type"):
            context.prepare_from_descriptor(descriptor)

    def test_local_context_prepare_from_descriptor_missing_file(self, tmp_path):
        """Test LocalContext.prepare_from_descriptor with missing file."""
        from rebuildr.stable_descriptor import StableFileInput
        
        # Create stable file input pointing to non-existent file
        stable_file = StableFileInput(
            target_path=Path("nonexistent.txt"),
            absolute_src_path=tmp_path / "nonexistent.txt"
        )
        
        descriptor = MagicMock()
        descriptor.inputs.files = [stable_file]
        descriptor.inputs.builders = []
        descriptor.inputs.external = []
        
        context = LocalContext(tmp_path)
        
        with pytest.raises(FileNotFoundError):
            context.prepare_from_descriptor(descriptor)


class TestContainersErrorHandling:
    def test_docker_bin_not_available(self):
        """Test docker_bin when docker is not available."""
        with patch('rebuildr.containers.docker.shutil.which', return_value=None):
            with pytest.raises(ValueError, match="docker is not available"):
                docker_bin()

    def test_docker_image_exists_locally_command_failure(self):
        """Test docker_image_exists_locally when command fails."""
        with patch('rebuildr.containers.docker.docker_bin') as mock_bin:
            mock_bin.return_value = Path("/usr/bin/docker")
            
            with patch('rebuildr.containers.docker.subprocess.run') as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(1, "docker")
                
                result = docker_image_exists_locally("test-image:latest")
                assert result is False

    def test_docker_image_exists_in_registry_dns_failure(self):
        """Test docker_image_exists_in_registry with DNS failure."""
        with patch('rebuildr.containers.docker.docker_bin') as mock_bin:
            mock_bin.return_value = Path("/usr/bin/docker")
            
            with patch('rebuildr.containers.docker.socket.gethostbyname') as mock_gethostbyname:
                mock_gethostbyname.side_effect = Exception("DNS resolution failed")
                
                result = docker_image_exists_in_registry("registry.example.com/image:latest")
                assert result is False

    def test_docker_image_exists_in_registry_http_failure(self):
        """Test docker_image_exists_in_registry with HTTP failure."""
        with patch('rebuildr.containers.docker.docker_bin') as mock_bin:
            mock_bin.return_value = Path("/usr/bin/docker")
            
            with patch('rebuildr.containers.docker.socket.gethostbyname') as mock_gethostbyname:
                mock_gethostbyname.return_value = "192.168.1.1"
                
                with patch('rebuildr.containers.docker.urllib.request.urlopen') as mock_urlopen:
                    mock_urlopen.side_effect = Exception("HTTP connection failed")
                    
                    result = docker_image_exists_in_registry("registry.example.com/image:latest")
                    assert result is False

    def test_docker_image_exists_in_registry_timeout(self):
        """Test docker_image_exists_in_registry with timeout."""
        with patch('rebuildr.containers.docker.docker_bin') as mock_bin:
            mock_bin.return_value = Path("/usr/bin/docker")
            
            with patch('rebuildr.containers.docker.subprocess.run') as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired("docker", 100)
                
                result = docker_image_exists_in_registry("registry.example.com/image:latest")
                assert result is False

    def test_docker_pull_image_failure(self):
        """Test docker_pull_image with command failure."""
        with patch('rebuildr.containers.docker.docker_bin') as mock_bin:
            mock_bin.return_value = Path("/usr/bin/docker")
            
            with patch('rebuildr.containers.docker.subprocess.run') as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(1, "docker")
                
                with pytest.raises(subprocess.CalledProcessError):
                    docker_pull_image("test-image:latest")

    def test_docker_push_image_failure(self):
        """Test docker_push_image with command failure."""
        with patch('rebuildr.containers.docker.docker_bin') as mock_bin:
            mock_bin.return_value = Path("/usr/bin/docker")
            
            with patch('rebuildr.containers.docker.docker_image_exists_in_registry') as mock_exists:
                mock_exists.return_value = False
                
                with patch('rebuildr.containers.docker.subprocess.run') as mock_run:
                    mock_run.side_effect = subprocess.CalledProcessError(1, "docker")
                    
                    with pytest.raises(subprocess.CalledProcessError):
                        docker_push_image("test-image:latest", overwrite_in_registry=False)


class TestBuildErrorHandling:
    def test_docker_cli_builder_build_failure(self):
        """Test DockerCLIBuilder.build with subprocess failure."""
        builder = DockerCLIBuilder()
        
        with patch('rebuildr.build.subprocess.Popen') as mock_popen:
            with patch('rebuildr.build.tempfile.mkstemp') as mock_mkstemp:
                mock_mkstemp.return_value = (1, "/tmp/iidfile")
                
                mock_process = MagicMock()
                mock_process.wait.return_value = 1
                mock_popen.return_value.__enter__.return_value = mock_process
                
                with pytest.raises(Exception, match="Builder exited with code 1"):
                    builder.build(
                        root_dir=Path("/tmp"),
                        dockerfile=Path("Dockerfile"),
                        tags=["test:latest"]
                    )

    def test_docker_cli_builder_invalid_iidfile(self):
        """Test DockerCLIBuilder.build with invalid iidfile content."""
        builder = DockerCLIBuilder()
        
        with patch('rebuildr.build.subprocess.Popen') as mock_popen:
            with patch('rebuildr.build.tempfile.mkstemp') as mock_mkstemp:
                mock_mkstemp.return_value = (1, "/tmp/iidfile")
                
                mock_process = MagicMock()
                mock_process.wait.return_value = 0
                mock_popen.return_value.__enter__.return_value = mock_process
                
                with patch('builtins.open', mock_open(read_data="invalid_content")):
                    with pytest.raises(Exception, match="stop"):
                        builder.build(
                            root_dir=Path("/tmp"),
                            dockerfile=Path("Dockerfile"),
                            tags=["test:latest"]
                        )


class TestToolsErrorHandling:
    def test_git_command_failure(self):
        """Test git_command with subprocess failure."""
        with patch('rebuildr.tools.git.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")
            
            with pytest.raises(subprocess.CalledProcessError):
                git_command(["invalid-git-command"])

    def test_git_command_failure_check_false(self):
        """Test git_command with check=False."""
        with patch('rebuildr.tools.git.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_run.return_value = mock_result
            
            result = git_command(["invalid-git-command"], check=False)
            assert result == mock_result

    def test_git_ls_remote_empty_output(self):
        """Test git_ls_remote with empty output."""
        with patch('rebuildr.tools.git.git_command') as mock_command:
            mock_result = MagicMock()
            mock_result.stdout = ""
            mock_command.return_value = mock_result
            
            with pytest.raises(ValueError, match="Ref .* not found"):
                git_ls_remote("https://github.com/test/repo.git", "nonexistent-ref")

    def test_git_ls_remote_whitespace_output(self):
        """Test git_ls_remote with whitespace-only output."""
        with patch('rebuildr.tools.git.git_command') as mock_command:
            mock_result = MagicMock()
            mock_result.stdout = "   \n\t  \n"
            mock_command.return_value = mock_result
            
            with pytest.raises(ValueError, match="Ref .* not found"):
                git_ls_remote("https://github.com/test/repo.git", "nonexistent-ref")


class TestStableDescriptorErrorHandling:
    def test_stable_descriptor_from_descriptor_not_absolute_path(self):
        """Test StableDescriptor.from_descriptor with non-absolute path."""
        descriptor = Descriptor(inputs=Inputs())
        
        with pytest.raises(ValueError, match="absolute_path must be absolute"):
            StableDescriptor.from_descriptor(descriptor, Path("relative/path"))

    def test_stable_descriptor_from_descriptor_missing_dockerfile(self, tmp_path):
        """Test StableDescriptor.from_descriptor with missing Dockerfile."""
        target = ImageTarget(
            repository="test-repo",
            tag="latest",
            dockerfile="nonexistent.Dockerfile"
        )
        
        descriptor = Descriptor(inputs=Inputs(), targets=[target])
        
        with pytest.raises(ValueError, match="Dockerfile .* does not exist"):
            StableDescriptor.from_descriptor(descriptor, tmp_path)

    def test_stable_descriptor_from_descriptor_glob_file_not_found(self, tmp_path):
        """Test StableDescriptor.from_descriptor with glob pattern matching non-existent files."""
        from rebuildr.descriptor import GlobInput
        
        glob_input = GlobInput(pattern="nonexistent*.txt")
        
        descriptor = Descriptor(inputs=Inputs(files=[glob_input]))
        
        with pytest.raises(ValueError, match="File .* does not exist"):
            StableDescriptor.from_descriptor(descriptor, tmp_path)

    def test_stable_descriptor_from_descriptor_unknown_external_type(self, tmp_path):
        """Test StableDescriptor.from_descriptor with unknown external input type."""
        descriptor = Descriptor(inputs=Inputs(external=[123]))  # Invalid type
        
        with pytest.raises(ValueError, match="Unexpected external input type"):
            StableDescriptor.from_descriptor(descriptor, tmp_path)

    def test_stable_descriptor_from_descriptor_string_external_not_supported(self, tmp_path):
        """Test StableDescriptor.from_descriptor with string external input."""
        descriptor = Descriptor(inputs=Inputs(external=["string-external"]))
        
        with pytest.raises(ValueError, match="str definition of external dependency is not yet supported"):
            StableDescriptor.from_descriptor(descriptor, tmp_path)

    def test_stable_descriptor_from_descriptor_unknown_target_type(self, tmp_path):
        """Test StableDescriptor.from_descriptor with unknown target type."""
        descriptor = Descriptor(inputs=Inputs(), targets=[123])  # Invalid type
        
        with pytest.raises(ValueError, match="Unexpected target type"):
            StableDescriptor.from_descriptor(descriptor, tmp_path)


class TestDescriptorValidationErrorHandling:
    def test_github_commit_input_empty_target_path(self):
        """Test GitHubCommitInput validation with empty target path."""
        with pytest.raises(ValueError, match="target_path must be set and not empty"):
            GitHubCommitInput(
                owner="test-owner",
                repo="test-repo",
                commit="abc123",
                target_path=""
            )

    def test_github_commit_input_root_target_path(self):
        """Test GitHubCommitInput validation with root target path."""
        with pytest.raises(ValueError, match="must not be the root directory"):
            GitHubCommitInput(
                owner="test-owner",
                repo="test-repo",
                commit="abc123",
                target_path="."
            )

    def test_git_repo_input_empty_target_path(self):
        """Test GitRepoInput validation with empty target path."""
        with pytest.raises(ValueError, match="target_path must be set and not empty"):
            GitRepoInput(
                url="https://github.com/test/repo.git",
                ref="main",
                target_path=""
            )

    def test_git_repo_input_root_target_path(self):
        """Test GitRepoInput validation with root target path."""
        with pytest.raises(ValueError, match="must not be the root directory"):
            GitRepoInput(
                url="https://github.com/test/repo.git",
                ref="main",
                target_path="/"
            )


class TestEdgeCases:
    def test_stable_file_input_read_bytes_permission_error(self, tmp_path):
        """Test StableFileInput.read_bytes with permission error."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        file_input = StableFileInput(
            target_path=Path("test.txt"),
            absolute_src_path=test_file
        )
        
        # Remove read permission
        test_file.chmod(0o000)
        
        try:
            with pytest.raises(PermissionError):
                file_input.read_bytes()
        finally:
            # Restore permission for cleanup
            test_file.chmod(0o644)

    def test_stable_file_input_hash_update_file_not_found(self):
        """Test StableFileInput.hash_update with non-existent file."""
        file_input = StableFileInput(
            target_path=Path("nonexistent.txt"),
            absolute_src_path=Path("/nonexistent/path.txt")
        )
        
        import hashlib
        hasher = hashlib.sha256()
        
        with pytest.raises(FileNotFoundError):
            file_input.hash_update(hasher)

    def test_stable_inputs_sha_sum_with_empty_inputs(self):
        """Test StableInputs.sha_sum with completely empty inputs."""
        from rebuildr.stable_descriptor import StableInputs, StableEnvironment
        
        inputs = StableInputs(envs=[], build_args=[], files=[], builders=[], external=[])
        env = StableEnvironment({}, {})
        
        sha = inputs.sha_sum(env)
        
        # Should still produce a valid SHA256 hash
        assert isinstance(sha, str)
        assert len(sha) == 64

    def test_stable_image_target_content_id_tag_with_none_platform(self, tmp_path):
        """Test StableImageTarget.content_id_tag with None platform."""
        from rebuildr.stable_descriptor import StableImageTarget, StableInputs, StableEnvironment
        
        inputs = StableInputs(envs=[], build_args=[], files=[], builders=[], external=[])
        env = StableEnvironment({}, {})
        
        target = StableImageTarget(
            repository="test-repo",
            dockerfile=Path("Dockerfile"),
            platform=None
        )
        
        content_id_tag = target.content_id_tag(inputs, env)
        
        assert content_id_tag.startswith("test-repo:src-id-")
        assert len(content_id_tag.split(":")[1]) == 64

    def test_stable_descriptor_stable_inputs_dict_with_none_values(self, tmp_path):
        """Test StableDescriptor.stable_inputs_dict with None values."""
        from rebuildr.stable_descriptor import (
            StableDescriptor, StableInputs, StableEnvInput, StableBuildArgsInput
        )
        
        env_input = StableEnvInput(key="TEST_VAR", default=None)
        build_arg_input = StableBuildArgsInput(key="BUILD_ARG", default=None)
        
        inputs = StableInputs(
            envs=[env_input],
            build_args=[build_arg_input],
            files=[],
            builders=[],
            external=[]
        )
        
        descriptor = StableDescriptor(
            absolute_path=tmp_path,
            inputs=inputs,
            targets=None
        )
        
        env = StableEnvironment({}, {})
        result = descriptor.stable_inputs_dict(env)
        
        # Should handle None values gracefully
        assert "inputs" in result
        assert "sha256" in result
        assert result["inputs"]["envs"][0]["key"] == "TEST_VAR"
        assert "value" not in result["inputs"]["envs"][0]
        assert result["inputs"]["build_args"][0]["key"] == "BUILD_ARG"
        assert "value" not in result["inputs"]["build_args"][0]

    def test_local_context_temp_directory_cleanup(self):
        """Test LocalContext temporary directory cleanup."""
        context = LocalContext.temp()
        temp_dir_path = context.temp_dir.name
        
        # Verify directory exists
        assert Path(temp_dir_path).exists()
        
        # Clean up
        context.temp_dir.cleanup()
        
        # Verify directory is gone
        assert not Path(temp_dir_path).exists()

    def test_parse_build_args_with_special_characters(self):
        """Test parse_build_args with special characters in values."""
        args = [
            "KEY1=value with spaces",
            "KEY2=value=with=equals",
            "KEY3=value\nwith\nnewlines",
            "KEY4=value\twith\ttabs"
        ]
        
        result = parse_build_args(args)
        
        assert result["KEY1"] == "value with spaces"
        assert result["KEY2"] == "value=with=equals"
        assert result["KEY3"] == "value\nwith\nnewlines"
        assert result["KEY4"] == "value\twith\ttabs"

    def test_parse_build_args_with_empty_values(self):
        """Test parse_build_args with empty values."""
        args = [
            "KEY1=",
            "KEY2=value",
            "KEY3="
        ]
        
        result = parse_build_args(args)
        
        assert result["KEY1"] == ""
        assert result["KEY2"] == "value"
        assert result["KEY3"] == ""

    def test_stable_descriptor_filter_env_and_build_args_with_missing_keys(self, tmp_path):
        """Test filter_env_and_build_args with missing keys."""
        from rebuildr.stable_descriptor import (
            StableDescriptor, StableInputs, StableEnvInput, StableBuildArgsInput
        )
        
        env_input = StableEnvInput(key="EXISTING_VAR")
        build_arg_input = StableBuildArgsInput(key="EXISTING_ARG")
        
        inputs = StableInputs(
            envs=[env_input],
            build_args=[build_arg_input],
            files=[],
            builders=[],
            external=[]
        )
        
        descriptor = StableDescriptor(
            absolute_path=tmp_path,
            inputs=inputs,
            targets=None
        )
        
        env = StableEnvironment(
            {"EXISTING_VAR": "value", "MISSING_VAR": "value"},
            {"EXISTING_ARG": "arg", "MISSING_ARG": "arg"}
        )
        
        filtered_env = descriptor.filter_env_and_build_args(env)
        
        # Should only include keys that are in the descriptor
        assert filtered_env.env == {"EXISTING_VAR": "value"}
        assert filtered_env.build_args == {"EXISTING_ARG": "arg"}