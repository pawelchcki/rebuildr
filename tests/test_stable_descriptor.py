import pytest
import hashlib
import os
import glob
from pathlib import Path, PurePath
from unittest.mock import patch, MagicMock

from rebuildr.stable_descriptor import (
    make_inner_relative_path,
    StableEnvironment,
    StableEnvInput,
    StableBuildArgsInput,
    StableGitHubCommitInput,
    StableGitRepoInput,
    StableFileInput,
    StableInputs,
    StableImageTarget,
    StableDescriptor,
    DescriptorEncoder,
)
from rebuildr.descriptor import (
    Descriptor,
    Inputs,
    FileInput,
    GlobInput,
    EnvInput,
    ArgsInput,
    GitHubCommitInput,
    GitRepoInput,
    ImageTarget,
    Platform,
)


class TestMakeInnerRelativePath:
    def test_make_inner_relative_path_absolute(self):
        """Test make_inner_relative_path with absolute path."""
        path = PurePath("/absolute/path/to/file.txt")
        result = make_inner_relative_path(path)
        assert result == PurePath("absolute/path/to/file.txt")

    def test_make_inner_relative_path_relative(self):
        """Test make_inner_relative_path with relative path."""
        path = PurePath("relative/path/to/file.txt")
        result = make_inner_relative_path(path)
        assert result == PurePath("relative/path/to/file.txt")

    def test_make_inner_relative_path_root(self):
        """Test make_inner_relative_path with root path."""
        path = PurePath("/")
        result = make_inner_relative_path(path)
        assert result == PurePath(".")

    def test_make_inner_relative_path_single_file(self):
        """Test make_inner_relative_path with single file."""
        path = PurePath("/file.txt")
        result = make_inner_relative_path(path)
        assert result == PurePath("file.txt")


class TestStableEnvironment:
    def test_stable_environment_initialization(self):
        """Test StableEnvironment initialization."""
        env = {"VAR1": "value1", "VAR2": "value2"}
        build_args = {"ARG1": "arg1", "ARG2": "arg2"}
        
        stable_env = StableEnvironment(env, build_args)
        assert stable_env.env == env
        assert stable_env.build_args == build_args

    def test_stable_environment_get_env(self):
        """Test get_env method."""
        env = {"VAR1": "value1", "VAR2": "value2"}
        build_args = {}
        
        stable_env = StableEnvironment(env, build_args)
        assert stable_env.get_env("VAR1") == "value1"
        assert stable_env.get_env("VAR2") == "value2"
        assert stable_env.get_env("NONEXISTENT") is None

    def test_stable_environment_get_build_arg(self):
        """Test get_build_arg method."""
        env = {}
        build_args = {"ARG1": "arg1", "ARG2": "arg2"}
        
        stable_env = StableEnvironment(env, build_args)
        assert stable_env.get_build_arg("ARG1") == "arg1"
        assert stable_env.get_build_arg("ARG2") == "arg2"
        assert stable_env.get_build_arg("NONEXISTENT") is None

    def test_stable_environment_from_os_env(self):
        """Test from_os_env static method."""
        with patch.dict(os.environ, {"VAR1": "value1", "VAR2": "value2"}):
            stable_env = StableEnvironment.from_os_env({"ARG1": "arg1"})
            
            assert stable_env.env == os.environ
            assert stable_env.build_args == {"ARG1": "arg1"}

    def test_stable_environment_from_os_env_no_build_args(self):
        """Test from_os_env static method without build args."""
        with patch.dict(os.environ, {"VAR1": "value1"}):
            stable_env = StableEnvironment.from_os_env()
            
            assert stable_env.env == os.environ
            assert stable_env.build_args == {}


class TestStableEnvInput:
    def test_stable_env_input_initialization(self):
        """Test StableEnvInput initialization."""
        env_input = StableEnvInput(key="TEST_VAR", default="default_value")
        assert env_input.key == "TEST_VAR"
        assert env_input.default == "default_value"

    def test_stable_env_input_sort_key(self):
        """Test sort_key method."""
        env_input = StableEnvInput(key="TEST_VAR")
        assert env_input.sort_key() == "TEST_VAR"

    def test_stable_env_input_hash_update_with_value(self):
        """Test hash_update method with environment value."""
        env_input = StableEnvInput(key="TEST_VAR")
        env = StableEnvironment({"TEST_VAR": "test_value"}, {})
        
        hasher = hashlib.sha256()
        env_input.hash_update(hasher, env)
        
        # Should include both key and value in hash
        expected_hash = hashlib.sha256()
        expected_hash.update("TEST_VAR".encode())
        expected_hash.update("test_value".encode())
        
        assert hasher.hexdigest() == expected_hash.hexdigest()

    def test_stable_env_input_hash_update_with_default(self):
        """Test hash_update method with default value."""
        env_input = StableEnvInput(key="TEST_VAR", default="default_value")
        env = StableEnvironment({}, {})  # No TEST_VAR in environment
        
        hasher = hashlib.sha256()
        env_input.hash_update(hasher, env)
        
        # Should include both key and default value in hash
        expected_hash = hashlib.sha256()
        expected_hash.update("TEST_VAR".encode())
        expected_hash.update("default_value".encode())
        
        assert hasher.hexdigest() == expected_hash.hexdigest()

    def test_stable_env_input_hash_update_empty_string(self):
        """Test hash_update method with empty string value."""
        env_input = StableEnvInput(key="TEST_VAR")
        env = StableEnvironment({"TEST_VAR": ""}, {})
        
        hasher = hashlib.sha256()
        env_input.hash_update(hasher, env)
        
        # Should include key but not empty value
        expected_hash = hashlib.sha256()
        expected_hash.update("TEST_VAR".encode())
        
        assert hasher.hexdigest() == expected_hash.hexdigest()

    def test_stable_env_input_hash_update_no_value_no_default(self):
        """Test hash_update method with no value and no default."""
        env_input = StableEnvInput(key="TEST_VAR")
        env = StableEnvironment({}, {})  # No TEST_VAR in environment
        
        hasher = hashlib.sha256()
        env_input.hash_update(hasher, env)
        
        # Should not include anything in hash
        expected_hash = hashlib.sha256()
        
        assert hasher.hexdigest() == expected_hash.hexdigest()


class TestStableBuildArgsInput:
    def test_stable_build_args_input_initialization(self):
        """Test StableBuildArgsInput initialization."""
        args_input = StableBuildArgsInput(key="BUILD_ARG", default="default_value")
        assert args_input.key == "BUILD_ARG"
        assert args_input.default == "default_value"

    def test_stable_build_args_input_sort_key(self):
        """Test sort_key method."""
        args_input = StableBuildArgsInput(key="BUILD_ARG")
        assert args_input.sort_key() == "BUILD_ARG"

    def test_stable_build_args_input_hash_update_with_value(self):
        """Test hash_update method with build arg value."""
        args_input = StableBuildArgsInput(key="BUILD_ARG")
        env = StableEnvironment({}, {"BUILD_ARG": "arg_value"})
        
        hasher = hashlib.sha256()
        args_input.hash_update(hasher, env)
        
        # Should include both key and value in hash
        expected_hash = hashlib.sha256()
        expected_hash.update("BUILD_ARG".encode())
        expected_hash.update("arg_value".encode())
        
        assert hasher.hexdigest() == expected_hash.hexdigest()

    def test_stable_build_args_input_hash_update_with_default(self):
        """Test hash_update method with default value."""
        args_input = StableBuildArgsInput(key="BUILD_ARG", default="default_arg")
        env = StableEnvironment({}, {})  # No BUILD_ARG in build args
        
        hasher = hashlib.sha256()
        args_input.hash_update(hasher, env)
        
        # Should include both key and default value in hash
        expected_hash = hashlib.sha256()
        expected_hash.update("BUILD_ARG".encode())
        expected_hash.update("default_arg".encode())
        
        assert hasher.hexdigest() == expected_hash.hexdigest()

    def test_stable_build_args_input_hash_update_no_value(self):
        """Test hash_update method with no value."""
        args_input = StableBuildArgsInput(key="BUILD_ARG")
        env = StableEnvironment({}, {})  # No BUILD_ARG in build args
        
        hasher = hashlib.sha256()
        args_input.hash_update(hasher, env)
        
        # Should not include anything in hash
        expected_hash = hashlib.sha256()
        
        assert hasher.hexdigest() == expected_hash.hexdigest()


class TestStableGitHubCommitInput:
    def test_stable_github_commit_input_initialization(self):
        """Test StableGitHubCommitInput initialization."""
        github_input = StableGitHubCommitInput(
            url="https://github.com/test/repo.git",
            commit="abc123",
            target_path=Path("external/repo")
        )
        assert github_input.url == "https://github.com/test/repo.git"
        assert github_input.commit == "abc123"
        assert github_input.target_path == Path("external/repo")

    def test_stable_github_commit_input_sort_key(self):
        """Test sort_key method."""
        github_input = StableGitHubCommitInput(
            url="https://github.com/test/repo.git",
            commit="abc123",
            target_path=Path("external/repo")
        )
        assert github_input.sort_key() == "abc123"

    def test_stable_github_commit_input_hash_update(self):
        """Test hash_update method."""
        github_input = StableGitHubCommitInput(
            url="https://github.com/test/repo.git",
            commit="abc123",
            target_path=Path("external/repo")
        )
        
        hasher = hashlib.sha256()
        github_input.hash_update(hasher)
        
        # Should include commit in hash
        expected_hash = hashlib.sha256()
        expected_hash.update("abc123".encode())
        
        assert hasher.hexdigest() == expected_hash.hexdigest()


class TestStableGitRepoInput:
    def test_stable_git_repo_input_initialization(self):
        """Test StableGitRepoInput initialization."""
        git_input = StableGitRepoInput(
            url="https://git.example.com/repo.git",
            commit="def456",
            target_path=Path("external/git-repo")
        )
        assert git_input.url == "https://git.example.com/repo.git"
        assert git_input.commit == "def456"
        assert git_input.target_path == Path("external/git-repo")

    def test_stable_git_repo_input_sort_key(self):
        """Test sort_key method."""
        git_input = StableGitRepoInput(
            url="https://git.example.com/repo.git",
            commit="def456",
            target_path=Path("external/git-repo")
        )
        assert git_input.sort_key() == "def456"

    def test_stable_git_repo_input_hash_update(self):
        """Test hash_update method."""
        git_input = StableGitRepoInput(
            url="https://git.example.com/repo.git",
            commit="def456",
            target_path=Path("external/git-repo")
        )
        
        hasher = hashlib.sha256()
        git_input.hash_update(hasher)
        
        # Should include commit in hash
        expected_hash = hashlib.sha256()
        expected_hash.update("def456".encode())
        
        assert hasher.hexdigest() == expected_hash.hexdigest()


class TestStableFileInput:
    def test_stable_file_input_initialization(self, tmp_path):
        """Test StableFileInput initialization."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        file_input = StableFileInput(
            target_path=Path("test.txt"),
            absolute_src_path=test_file,
            ignore_target_path=False
        )
        assert file_input.target_path == Path("test.txt")
        assert file_input.absolute_src_path == test_file
        assert file_input.ignore_target_path is False

    def test_stable_file_input_sort_key(self, tmp_path):
        """Test sort_key method."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        file_input = StableFileInput(
            target_path=Path("test.txt"),
            absolute_src_path=test_file
        )
        assert file_input.sort_key() == "test.txt"

    def test_stable_file_input_read_bytes(self, tmp_path):
        """Test read_bytes method."""
        test_content = "test content"
        test_file = tmp_path / "test.txt"
        test_file.write_text(test_content)
        
        file_input = StableFileInput(
            target_path=Path("test.txt"),
            absolute_src_path=test_file
        )
        
        content = file_input.read_bytes()
        assert content.decode() == test_content

    def test_stable_file_input_hash_update(self, tmp_path):
        """Test hash_update method."""
        test_content = "test content"
        test_file = tmp_path / "test.txt"
        test_file.write_text(test_content)
        
        file_input = StableFileInput(
            target_path=Path("test.txt"),
            absolute_src_path=test_file
        )
        
        hasher = hashlib.sha256()
        file_input.hash_update(hasher)
        
        # Should include target path and content in hash
        expected_hash = hashlib.sha256()
        expected_hash.update("test.txt".encode())
        expected_hash.update(test_content.encode())
        
        assert hasher.hexdigest() == expected_hash.hexdigest()

    def test_stable_file_input_hash_update_ignore_target_path(self, tmp_path):
        """Test hash_update method with ignore_target_path=True."""
        test_content = "test content"
        test_file = tmp_path / "test.txt"
        test_file.write_text(test_content)
        
        file_input = StableFileInput(
            target_path=Path("test.txt"),
            absolute_src_path=test_file,
            ignore_target_path=True
        )
        
        hasher = hashlib.sha256()
        file_input.hash_update(hasher)
        
        # Should include only content in hash, not target path
        expected_hash = hashlib.sha256()
        expected_hash.update(test_content.encode())
        
        assert hasher.hexdigest() == expected_hash.hexdigest()

    def test_stable_file_input_hash_update_with_permissions(self, tmp_path):
        """Test hash_update method with non-default permissions."""
        test_content = "test content"
        test_file = tmp_path / "test.txt"
        test_file.write_text(test_content)
        test_file.chmod(0o755)  # Non-default permissions
        
        file_input = StableFileInput(
            target_path=Path("test.txt"),
            absolute_src_path=test_file
        )
        
        hasher = hashlib.sha256()
        file_input.hash_update(hasher)
        
        # Should include target path, permissions, and content in hash
        expected_hash = hashlib.sha256()
        expected_hash.update("test.txt".encode())
        expected_hash.update(str(test_file.stat().st_mode).encode())
        expected_hash.update(test_content.encode())
        
        assert hasher.hexdigest() == expected_hash.hexdigest()

    def test_stable_file_input_make_stable(self, tmp_path):
        """Test make_stable static method."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        file_input = FileInput(path="test.txt", target_path="dest/test.txt")
        
        stable_file = StableFileInput.make_stable(tmp_path, file_input)
        
        assert stable_file.target_path == Path("dest/test.txt")
        assert stable_file.absolute_src_path == tmp_path / "test.txt"

    def test_stable_file_input_make_stable_no_target_path(self, tmp_path):
        """Test make_stable static method without target_path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        file_input = FileInput(path="test.txt")
        
        stable_file = StableFileInput.make_stable(tmp_path, file_input)
        
        assert stable_file.target_path == Path("test.txt")
        assert stable_file.absolute_src_path == tmp_path / "test.txt"


class TestStableInputs:
    def test_stable_inputs_initialization(self):
        """Test StableInputs initialization."""
        inputs = StableInputs(
            envs=[StableEnvInput(key="TEST_VAR")],
            build_args=[StableBuildArgsInput(key="BUILD_ARG")],
            files=[],
            builders=[],
            external=[]
        )
        assert len(inputs.envs) == 1
        assert len(inputs.build_args) == 1
        assert len(inputs.files) == 0
        assert len(inputs.builders) == 0
        assert len(inputs.external) == 0

    def test_stable_inputs_sha_sum(self, tmp_path):
        """Test sha_sum method."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file1.write_text("content1")
        
        file2 = tmp_path / "file2.txt"
        file2.write_text("content2")
        
        # Create stable inputs
        env_input = StableEnvInput(key="TEST_VAR")
        build_arg_input = StableBuildArgsInput(key="BUILD_ARG")
        file_input1 = StableFileInput(
            target_path=Path("file1.txt"),
            absolute_src_path=file1
        )
        file_input2 = StableFileInput(
            target_path=Path("file2.txt"),
            absolute_src_path=file2
        )
        
        inputs = StableInputs(
            envs=[env_input],
            build_args=[build_arg_input],
            files=[file_input1, file_input2],
            builders=[],
            external=[]
        )
        
        env = StableEnvironment({"TEST_VAR": "test_value"}, {"BUILD_ARG": "build_value"})
        
        sha = inputs.sha_sum(env)
        assert isinstance(sha, str)
        assert len(sha) == 64  # SHA256 hex length

    def test_stable_inputs_sha_sum_deterministic(self, tmp_path):
        """Test that sha_sum is deterministic."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file1.write_text("content1")
        
        # Create stable inputs
        env_input = StableEnvInput(key="TEST_VAR")
        file_input = StableFileInput(
            target_path=Path("file1.txt"),
            absolute_src_path=file1
        )
        
        inputs = StableInputs(
            envs=[env_input],
            build_args=[],
            files=[file_input],
            builders=[],
            external=[]
        )
        
        env = StableEnvironment({"TEST_VAR": "test_value"}, {})
        
        sha1 = inputs.sha_sum(env)
        sha2 = inputs.sha_sum(env)
        
        assert sha1 == sha2

    def test_stable_inputs_find_file(self, tmp_path):
        """Test find_file method."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("content1")
        
        file_input = StableFileInput(
            target_path=Path("file1.txt"),
            absolute_src_path=file1
        )
        
        inputs = StableInputs(
            envs=[],
            build_args=[],
            files=[file_input],
            builders=[],
            external=[]
        )
        
        found = inputs.find_file(Path("file1.txt"))
        assert found == file_input
        
        not_found = inputs.find_file(Path("nonexistent.txt"))
        assert not_found is None

    def test_stable_inputs_find_file_in_builders(self, tmp_path):
        """Test find_file method in builders."""
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM alpine")
        
        builder_file = StableFileInput(
            target_path=Path("Dockerfile"),
            absolute_src_path=dockerfile
        )
        
        inputs = StableInputs(
            envs=[],
            build_args=[],
            files=[],
            builders=[builder_file],
            external=[]
        )
        
        found = inputs.find_file(Path("Dockerfile"))
        assert found == builder_file


class TestStableImageTarget:
    def test_stable_image_target_initialization(self):
        """Test StableImageTarget initialization."""
        target = StableImageTarget(
            repository="test-repo",
            dockerfile=Path("Dockerfile"),
            tag="latest",
            also_tag_with_content_id=True,
            platform=Platform.LINUX_AMD64
        )
        assert target.repository == "test-repo"
        assert target.dockerfile == Path("Dockerfile")
        assert target.tag == "latest"
        assert target.also_tag_with_content_id is True
        assert target.platform == Platform.LINUX_AMD64

    def test_stable_image_target_image_tags(self, tmp_path):
        """Test image_tags method."""
        # Create test file for inputs
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        file_input = StableFileInput(
            target_path=Path("test.txt"),
            absolute_src_path=test_file
        )
        
        inputs = StableInputs(
            envs=[],
            build_args=[],
            files=[file_input],
            builders=[],
            external=[]
        )
        
        env = StableEnvironment({}, {})
        
        target = StableImageTarget(
            repository="test-repo",
            dockerfile=Path("Dockerfile"),
            tag="latest",
            also_tag_with_content_id=True
        )
        
        tags = target.image_tags(inputs, env)
        
        assert len(tags) == 2
        assert "test-repo:latest" in tags
        assert any("test-repo:src-id-" in tag for tag in tags)

    def test_stable_image_target_image_tags_no_content_id(self, tmp_path):
        """Test image_tags method without content ID tagging."""
        target = StableImageTarget(
            repository="test-repo",
            dockerfile=Path("Dockerfile"),
            tag="latest",
            also_tag_with_content_id=False
        )
        
        inputs = StableInputs(envs=[], build_args=[], files=[], builders=[], external=[])
        env = StableEnvironment({}, {})
        
        tags = target.image_tags(inputs, env)
        
        assert len(tags) == 1
        assert "test-repo:latest" in tags

    def test_stable_image_target_image_tags_no_tag(self, tmp_path):
        """Test image_tags method without explicit tag."""
        target = StableImageTarget(
            repository="test-repo",
            dockerfile=Path("Dockerfile"),
            tag=None,
            also_tag_with_content_id=True
        )
        
        inputs = StableInputs(envs=[], build_args=[], files=[], builders=[], external=[])
        env = StableEnvironment({}, {})
        
        tags = target.image_tags(inputs, env)
        
        assert len(tags) == 1
        assert any("test-repo:src-id-" in tag for tag in tags)

    def test_stable_image_target_content_id_tag(self, tmp_path):
        """Test content_id_tag method."""
        # Create test file for inputs
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        file_input = StableFileInput(
            target_path=Path("test.txt"),
            absolute_src_path=test_file
        )
        
        inputs = StableInputs(
            envs=[],
            build_args=[],
            files=[file_input],
            builders=[],
            external=[]
        )
        
        env = StableEnvironment({}, {})
        
        target = StableImageTarget(
            repository="test-repo",
            dockerfile=Path("Dockerfile")
        )
        
        content_id_tag = target.content_id_tag(inputs, env)
        
        assert content_id_tag.startswith("test-repo:src-id-")
        # The content ID includes "src-id-" prefix, so we check the SHA256 part
        sha_part = content_id_tag.split(":")[1].split("-")[-1]
        assert len(sha_part) == 64  # SHA256 hex length

    def test_stable_image_target_content_id_tag_with_platform(self, tmp_path):
        """Test content_id_tag method with platform."""
        # Create test file for inputs
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        file_input = StableFileInput(
            target_path=Path("test.txt"),
            absolute_src_path=test_file
        )
        
        inputs = StableInputs(
            envs=[],
            build_args=[],
            files=[file_input],
            builders=[],
            external=[]
        )
        
        env = StableEnvironment({}, {})
        
        target = StableImageTarget(
            repository="test-repo",
            dockerfile=Path("Dockerfile"),
            platform=Platform.LINUX_ARM64
        )
        
        content_id_tag = target.content_id_tag(inputs, env)
        
        assert content_id_tag.startswith("test-repo:linux-arm64-src-id-")
        # The content ID includes "linux-arm64-src-id-" prefix, so we check the SHA256 part
        sha_part = content_id_tag.split(":")[1].split("-")[-1]
        assert len(sha_part) == 64  # SHA256 hex length


class TestStableDescriptor:
    def test_stable_descriptor_initialization(self, tmp_path):
        """Test StableDescriptor initialization."""
        inputs = StableInputs(envs=[], build_args=[], files=[], builders=[], external=[])
        
        descriptor = StableDescriptor(
            absolute_path=tmp_path,
            inputs=inputs,
            targets=None
        )
        
        assert descriptor.absolute_path == tmp_path
        assert descriptor.inputs == inputs
        assert descriptor.targets is None

    def test_stable_descriptor_sha_sum(self, tmp_path):
        """Test sha_sum method."""
        inputs = StableInputs(envs=[], build_args=[], files=[], builders=[], external=[])
        
        descriptor = StableDescriptor(
            absolute_path=tmp_path,
            inputs=inputs,
            targets=None
        )
        
        env = StableEnvironment({}, {})
        sha = descriptor.sha_sum(env)
        
        assert isinstance(sha, str)
        assert len(sha) == 64  # SHA256 hex length

    def test_stable_descriptor_stable_inputs_dict(self, tmp_path):
        """Test stable_inputs_dict method."""
        env_input = StableEnvInput(key="TEST_VAR", default="default_value")
        build_arg_input = StableBuildArgsInput(key="BUILD_ARG", default="default_arg")
        
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
        
        env = StableEnvironment({"TEST_VAR": "test_value"}, {"BUILD_ARG": "build_value"})
        result = descriptor.stable_inputs_dict(env)
        
        assert "inputs" in result
        assert "sha256" in result
        assert result["inputs"]["envs"][0]["key"] == "TEST_VAR"
        assert result["inputs"]["envs"][0]["value"] == "test_value"
        assert result["inputs"]["build_args"][0]["key"] == "BUILD_ARG"
        assert result["inputs"]["build_args"][0]["value"] == "build_value"

    def test_stable_descriptor_stable_inputs_dict_no_values(self, tmp_path):
        """Test stable_inputs_dict method without environment values."""
        env_input = StableEnvInput(key="TEST_VAR", default="default_value")
        build_arg_input = StableBuildArgsInput(key="BUILD_ARG", default="default_arg")
        
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
        
        env = StableEnvironment({}, {})  # No values provided
        result = descriptor.stable_inputs_dict(env)
        
        assert "inputs" in result
        assert "sha256" in result
        assert result["inputs"]["envs"][0]["key"] == "TEST_VAR"
        assert "value" not in result["inputs"]["envs"][0]
        assert result["inputs"]["build_args"][0]["key"] == "BUILD_ARG"
        assert "value" not in result["inputs"]["build_args"][0]

    def test_stable_descriptor_filter_env_and_build_args(self, tmp_path):
        """Test filter_env_and_build_args method."""
        env_input = StableEnvInput(key="TEST_VAR")
        build_arg_input = StableBuildArgsInput(key="BUILD_ARG")
        
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
            {"TEST_VAR": "test_value", "OTHER_VAR": "other_value"},
            {"BUILD_ARG": "build_value", "OTHER_ARG": "other_arg"}
        )
        
        filtered_env = descriptor.filter_env_and_build_args(env)
        
        assert filtered_env.env == {"TEST_VAR": "test_value"}
        assert filtered_env.build_args == {"BUILD_ARG": "build_value"}

    @patch('rebuildr.stable_descriptor.glob.glob')
    def test_stable_descriptor_make_stable_files(self, mock_glob, tmp_path):
        """Test _make_stable_files static method."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file1.write_text("content1")
        
        file2 = tmp_path / "file2.txt"
        file2.write_text("content2")
        
        # Mock glob to return file paths
        mock_glob.return_value = ["file1.txt", "file2.txt"]
        
        glob_input = GlobInput(pattern="*.txt", root_dir=".")
        
        stable_files = StableDescriptor._make_stable_files([glob_input], tmp_path)
        
        assert len(stable_files) == 2
        assert all(isinstance(f, StableFileInput) for f in stable_files)
        assert mock_glob.called

    def test_stable_descriptor_make_stable_files_file_input(self, tmp_path):
        """Test _make_stable_files with FileInput."""
        file_input = FileInput(path="test.txt", target_path="dest/test.txt")
        
        stable_files = StableDescriptor._make_stable_files([file_input], tmp_path)
        
        assert len(stable_files) == 1
        assert isinstance(stable_files[0], StableFileInput)
        assert stable_files[0].target_path == Path("dest/test.txt")

    def test_stable_descriptor_make_stable_files_string_input(self, tmp_path):
        """Test _make_stable_files with string input."""
        stable_files = StableDescriptor._make_stable_files(["test.txt"], tmp_path)
        
        assert len(stable_files) == 1
        assert isinstance(stable_files[0], StableFileInput)
        assert stable_files[0].target_path == Path("test.txt")

    def test_stable_descriptor_make_stable_files_unknown_type(self, tmp_path):
        """Test _make_stable_files with unknown input type."""
        with pytest.raises(ValueError, match="Unexpected input type"):
            StableDescriptor._make_stable_files([123], tmp_path)

    @patch('rebuildr.stable_descriptor.git_ls_remote')
    def test_stable_descriptor_from_descriptor(self, mock_git_ls_remote, tmp_path):
        """Test from_descriptor static method."""
        mock_git_ls_remote.return_value = "abc123"
        
        # Create test files
        file1 = tmp_path / "file1.txt"
        file1.write_text("content1")
        
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM alpine")
        
        # Create descriptor
        file_input = FileInput(path="file1.txt", target_path="dest/file1.txt")
        env_input = EnvInput(key="TEST_VAR", default="default_value")
        dockerfile_input = FileInput(path="Dockerfile")
        git_input = GitRepoInput(
            url="https://github.com/test/repo.git",
            ref="main",
            target_path="external/repo"
        )
        
        inputs = Inputs(
            files=[file_input],
            builders=[env_input, dockerfile_input],
            external=[git_input]
        )
        
        target = ImageTarget(
            repository="test-repo",
            tag="latest",
            dockerfile="Dockerfile"
        )
        
        descriptor = Descriptor(inputs=inputs, targets=[target])
        
        stable_descriptor = StableDescriptor.from_descriptor(descriptor, tmp_path)
        
        assert isinstance(stable_descriptor, StableDescriptor)
        assert stable_descriptor.absolute_path == tmp_path
        assert len(stable_descriptor.inputs.files) == 1
        assert len(stable_descriptor.inputs.builders) == 2  # env + dockerfile
        assert len(stable_descriptor.inputs.external) == 1
        assert len(stable_descriptor.targets) == 1

    def test_stable_descriptor_from_descriptor_not_absolute_path(self):
        """Test from_descriptor with non-absolute path."""
        descriptor = Descriptor(inputs=Inputs())
        
        with pytest.raises(ValueError, match="absolute_path must be absolute"):
            StableDescriptor.from_descriptor(descriptor, Path("relative/path"))

    def test_stable_descriptor_from_descriptor_missing_dockerfile(self, tmp_path):
        """Test from_descriptor with missing Dockerfile."""
        target = ImageTarget(
            repository="test-repo",
            tag="latest",
            dockerfile="nonexistent.Dockerfile"
        )
        
        descriptor = Descriptor(inputs=Inputs(), targets=[target])
        
        with pytest.raises(ValueError, match="Dockerfile .* does not exist"):
            StableDescriptor.from_descriptor(descriptor, tmp_path)


class TestDescriptorEncoder:
    def test_descriptor_encoder_pureposixpath(self):
        """Test DescriptorEncoder with PurePosixPath."""
        encoder = DescriptorEncoder()
        
        path = PurePath("test/path")
        result = encoder.default(path)
        
        assert result == "test/path"

    def test_descriptor_encoder_other_type(self):
        """Test DescriptorEncoder with other types."""
        encoder = DescriptorEncoder()
        
        # Should fall back to default JSON encoder, which raises TypeError for non-serializable types
        with pytest.raises(TypeError, match="Object of type str is not JSON serializable"):
            encoder.default("test_string")
        
        with pytest.raises(TypeError, match="Object of type int is not JSON serializable"):
            encoder.default(123)