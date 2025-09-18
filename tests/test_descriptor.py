import pytest
from pathlib import PurePath

from rebuildr.descriptor import (
    FileInput,
    GlobInput,
    EnvInput,
    ArgsInput,
    GitHubCommitInput,
    GitRepoInput,
    Inputs,
    Platform,
    ImageTarget,
    Descriptor,
)


class TestFileInput:
    def test_file_input_basic(self):
        """Test basic FileInput creation."""
        file_input = FileInput(path="test.txt")
        assert file_input.path == "test.txt"
        assert file_input.target_path is None

    def test_file_input_with_target_path(self):
        """Test FileInput with target path."""
        file_input = FileInput(path="src/test.txt", target_path="dest/test.txt")
        assert file_input.path == "src/test.txt"
        assert file_input.target_path == "dest/test.txt"

    def test_file_input_with_purepath(self):
        """Test FileInput with PurePath."""
        path = PurePath("src/test.txt")
        target_path = PurePath("dest/test.txt")
        
        file_input = FileInput(path=path, target_path=target_path)
        assert file_input.path == path
        assert file_input.target_path == target_path


class TestGlobInput:
    def test_glob_input_basic(self):
        """Test basic GlobInput creation."""
        glob_input = GlobInput(pattern="*.txt")
        assert glob_input.pattern == "*.txt"
        assert glob_input.root_dir is None
        assert glob_input.target_path is None

    def test_glob_input_with_root_dir(self):
        """Test GlobInput with root directory."""
        glob_input = GlobInput(pattern="*.txt", root_dir="src")
        assert glob_input.pattern == "*.txt"
        assert glob_input.root_dir == "src"
        assert glob_input.target_path is None

    def test_glob_input_with_target_path(self):
        """Test GlobInput with target path."""
        glob_input = GlobInput(pattern="*.txt", target_path="dest")
        assert glob_input.pattern == "*.txt"
        assert glob_input.root_dir is None
        assert glob_input.target_path == "dest"

    def test_glob_input_with_purepath(self):
        """Test GlobInput with PurePath."""
        root_dir = PurePath("src")
        target_path = PurePath("dest")
        
        glob_input = GlobInput(pattern="*.txt", root_dir=root_dir, target_path=target_path)
        assert glob_input.pattern == "*.txt"
        assert glob_input.root_dir == root_dir
        assert glob_input.target_path == target_path


class TestEnvInput:
    def test_env_input_basic(self):
        """Test basic EnvInput creation."""
        env_input = EnvInput(key="TEST_VAR")
        assert env_input.key == "TEST_VAR"
        assert env_input.default is None

    def test_env_input_with_default(self):
        """Test EnvInput with default value."""
        env_input = EnvInput(key="TEST_VAR", default="default_value")
        assert env_input.key == "TEST_VAR"
        assert env_input.default == "default_value"


class TestArgsInput:
    def test_args_input_basic(self):
        """Test basic ArgsInput creation."""
        args_input = ArgsInput(key="build_arg")
        assert args_input.key == "build_arg"
        assert args_input.default is None

    def test_args_input_with_default(self):
        """Test ArgsInput with default value."""
        args_input = ArgsInput(key="build_arg", default="default_value")
        assert args_input.key == "build_arg"
        assert args_input.default == "default_value"


class TestGitHubCommitInput:
    def test_github_commit_input_basic(self):
        """Test basic GitHubCommitInput creation."""
        github_input = GitHubCommitInput(
            owner="test-owner",
            repo="test-repo",
            commit="abc123",
            target_path="src/repo"
        )
        assert github_input.owner == "test-owner"
        assert github_input.repo == "test-repo"
        assert github_input.commit == "abc123"
        assert github_input.target_path == "src/repo"

    def test_github_commit_input_with_purepath(self):
        """Test GitHubCommitInput with PurePath target."""
        target_path = PurePath("src/repo")
        github_input = GitHubCommitInput(
            owner="test-owner",
            repo="test-repo",
            commit="abc123",
            target_path=target_path
        )
        assert github_input.target_path == target_path

    def test_github_commit_input_validation_empty_target_path(self):
        """Test GitHubCommitInput validation with empty target path."""
        with pytest.raises(ValueError, match="target_path must be set and not empty"):
            GitHubCommitInput(
                owner="test-owner",
                repo="test-repo",
                commit="abc123",
                target_path=""
            )

    def test_github_commit_input_validation_root_target_path(self):
        """Test GitHubCommitInput validation with root target path."""
        with pytest.raises(ValueError, match="must not be the root directory"):
            GitHubCommitInput(
                owner="test-owner",
                repo="test-repo",
                commit="abc123",
                target_path="."
            )


class TestGitRepoInput:
    def test_git_repo_input_basic(self):
        """Test basic GitRepoInput creation."""
        git_input = GitRepoInput(
            url="https://github.com/test/repo.git",
            ref="main",
            target_path="src/repo"
        )
        assert git_input.url == "https://github.com/test/repo.git"
        assert git_input.ref == "main"
        assert git_input.target_path == "src/repo"

    def test_git_repo_input_with_purepath(self):
        """Test GitRepoInput with PurePath target."""
        target_path = PurePath("src/repo")
        git_input = GitRepoInput(
            url="https://github.com/test/repo.git",
            ref="main",
            target_path=target_path
        )
        assert git_input.target_path == target_path

    def test_git_repo_input_validation_empty_target_path(self):
        """Test GitRepoInput validation with empty target path."""
        with pytest.raises(ValueError, match="target_path must be set and not empty"):
            GitRepoInput(
                url="https://github.com/test/repo.git",
                ref="main",
                target_path=""
            )

    def test_git_repo_input_validation_root_target_path(self):
        """Test GitRepoInput validation with root target path."""
        with pytest.raises(ValueError, match="must not be the root directory"):
            GitRepoInput(
                url="https://github.com/test/repo.git",
                ref="main",
                target_path="/"
            )


class TestInputs:
    def test_inputs_empty(self):
        """Test empty Inputs creation."""
        inputs = Inputs()
        assert inputs.files == []
        assert inputs.builders == []
        assert inputs.external == []

    def test_inputs_with_files(self):
        """Test Inputs with file inputs."""
        file_input = FileInput(path="test.txt")
        inputs = Inputs(files=[file_input])
        assert len(inputs.files) == 1
        assert inputs.files[0] == file_input

    def test_inputs_with_builders(self):
        """Test Inputs with builder inputs."""
        env_input = EnvInput(key="TEST_VAR")
        file_input = FileInput(path="Dockerfile")
        inputs = Inputs(builders=[env_input, file_input])
        assert len(inputs.builders) == 2
        assert inputs.builders[0] == env_input
        assert inputs.builders[1] == file_input

    def test_inputs_with_external(self):
        """Test Inputs with external inputs."""
        github_input = GitHubCommitInput(
            owner="test-owner",
            repo="test-repo",
            commit="abc123",
            target_path="src/repo"
        )
        inputs = Inputs(external=[github_input])
        assert len(inputs.external) == 1
        assert inputs.external[0] == github_input

    def test_inputs_mixed_types(self):
        """Test Inputs with mixed input types."""
        file_input = FileInput(path="test.txt")
        env_input = EnvInput(key="TEST_VAR")
        github_input = GitHubCommitInput(
            owner="test-owner",
            repo="test-repo",
            commit="abc123",
            target_path="src/repo"
        )
        
        inputs = Inputs(
            files=[file_input],
            builders=[env_input],
            external=[github_input]
        )
        
        assert len(inputs.files) == 1
        assert len(inputs.builders) == 1
        assert len(inputs.external) == 1


class TestPlatform:
    def test_platform_values(self):
        """Test Platform enum values."""
        assert Platform.LINUX_AMD64.value == "linux/amd64"
        assert Platform.LINUX_ARM64.value == "linux/arm64"

    def test_platform_enum_membership(self):
        """Test Platform enum membership."""
        assert "linux/amd64" in [p.value for p in Platform]
        assert "linux/arm64" in [p.value for p in Platform]


class TestImageTarget:
    def test_image_target_basic(self):
        """Test basic ImageTarget creation."""
        target = ImageTarget(repository="test-repo")
        assert target.repository == "test-repo"
        assert target.tag is None
        assert target.also_tag_with_content_id is True
        assert target.dockerfile is None
        assert target.platform is None
        assert target.target is None

    def test_image_target_with_tag(self):
        """Test ImageTarget with tag."""
        target = ImageTarget(repository="test-repo", tag="latest")
        assert target.repository == "test-repo"
        assert target.tag == "latest"

    def test_image_target_with_dockerfile(self):
        """Test ImageTarget with dockerfile."""
        target = ImageTarget(repository="test-repo", dockerfile="custom.Dockerfile")
        assert target.repository == "test-repo"
        assert target.dockerfile == "custom.Dockerfile"

    def test_image_target_with_platform(self):
        """Test ImageTarget with platform."""
        target = ImageTarget(repository="test-repo", platform=Platform.LINUX_AMD64)
        assert target.repository == "test-repo"
        assert target.platform == Platform.LINUX_AMD64

    def test_image_target_with_platform_string(self):
        """Test ImageTarget with platform as string."""
        target = ImageTarget(repository="test-repo", platform="linux/amd64")
        assert target.repository == "test-repo"
        assert target.platform == "linux/amd64"

    def test_image_target_with_purepath_dockerfile(self):
        """Test ImageTarget with PurePath dockerfile."""
        dockerfile = PurePath("custom.Dockerfile")
        target = ImageTarget(repository="test-repo", dockerfile=dockerfile)
        assert target.repository == "test-repo"
        assert target.dockerfile == dockerfile

    def test_image_target_disable_content_id_tag(self):
        """Test ImageTarget with content ID tagging disabled."""
        target = ImageTarget(repository="test-repo", also_tag_with_content_id=False)
        assert target.repository == "test-repo"
        assert target.also_tag_with_content_id is False


class TestDescriptor:
    def test_descriptor_basic(self):
        """Test basic Descriptor creation."""
        inputs = Inputs()
        descriptor = Descriptor(inputs=inputs)
        assert descriptor.inputs == inputs
        assert descriptor.targets is None

    def test_descriptor_with_targets(self):
        """Test Descriptor with targets."""
        inputs = Inputs()
        target = ImageTarget(repository="test-repo", tag="latest")
        descriptor = Descriptor(inputs=inputs, targets=[target])
        assert descriptor.inputs == inputs
        assert len(descriptor.targets) == 1
        assert descriptor.targets[0] == target

    def test_descriptor_with_multiple_targets(self):
        """Test Descriptor with multiple targets."""
        inputs = Inputs()
        target1 = ImageTarget(repository="test-repo1", tag="latest")
        target2 = ImageTarget(repository="test-repo2", tag="v1.0")
        descriptor = Descriptor(inputs=inputs, targets=[target1, target2])
        assert descriptor.inputs == inputs
        assert len(descriptor.targets) == 2
        assert descriptor.targets[0] == target1
        assert descriptor.targets[1] == target2

    def test_descriptor_complete_example(self):
        """Test Descriptor with complete example."""
        file_input = FileInput(path="src/app.py", target_path="app.py")
        env_input = EnvInput(key="ENV_VAR", default="default_value")
        dockerfile_input = FileInput(path="Dockerfile")
        github_input = GitHubCommitInput(
            owner="test-owner",
            repo="test-repo",
            commit="abc123",
            target_path="external/repo"
        )
        
        inputs = Inputs(
            files=[file_input],
            builders=[env_input, dockerfile_input],
            external=[github_input]
        )
        
        target = ImageTarget(
            repository="my-app",
            tag="latest",
            dockerfile="Dockerfile",
            platform=Platform.LINUX_AMD64
        )
        
        descriptor = Descriptor(inputs=inputs, targets=[target])
        
        assert len(descriptor.inputs.files) == 1
        assert len(descriptor.inputs.builders) == 2
        assert len(descriptor.inputs.external) == 1
        assert len(descriptor.targets) == 1
        assert descriptor.targets[0].repository == "my-app"