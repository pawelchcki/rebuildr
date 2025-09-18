import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from rebuildr.tools.git import (
    git_command,
    git_clone,
    git_better_clone,
    git_checkout,
    git_ls_remote,
)
from rebuildr.tools.docker_git_repo_as_layer import dockerfile_parametrized


class TestGitCommand:
    @patch('rebuildr.tools.git.subprocess.run')
    def test_git_command_basic(self, mock_run):
        """Test basic git command execution."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = git_command(["status"])
        
        mock_run.assert_called_once_with(
            ["git", "status"],
            check=True
        )
        assert result == mock_run.return_value

    @patch('rebuildr.tools.git.subprocess.run')
    def test_git_command_with_kwargs(self, mock_run):
        """Test git command with additional kwargs."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = git_command(
            ["commit", "-m", "test"],
            cwd="/tmp",
            capture_output=True,
            text=True
        )
        
        mock_run.assert_called_once_with(
            ["git", "commit", "-m", "test"],
            check=True,
            cwd="/tmp",
            capture_output=True,
            text=True
        )

    @patch('rebuildr.tools.git.subprocess.run')
    def test_git_command_override_check(self, mock_run):
        """Test git command with check=False."""
        mock_run.return_value = MagicMock(returncode=1)
        
        result = git_command(["invalid"], check=False)
        
        mock_run.assert_called_once_with(
            ["git", "invalid"],
            check=False
        )

    @patch('rebuildr.tools.git.subprocess.run')
    def test_git_command_exception(self, mock_run):
        """Test git command raises exception on failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        
        with pytest.raises(subprocess.CalledProcessError):
            git_command(["invalid"])


class TestGitClone:
    @patch('rebuildr.tools.git.git_command')
    @patch('rebuildr.tools.git.git_checkout')
    def test_git_clone_basic(self, mock_checkout, mock_command):
        """Test basic git clone functionality."""
        url = "https://github.com/test/repo.git"
        target_path = Path("/tmp/repo")
        ref = "main"
        
        git_clone(url, target_path, ref)
        
        mock_command.assert_called_once_with(["clone", url, str(target_path)])
        mock_checkout.assert_called_once_with(target_path, ref)

    @patch('rebuildr.tools.git.git_command')
    @patch('rebuildr.tools.git.git_checkout')
    def test_git_clone_with_different_ref(self, mock_checkout, mock_command):
        """Test git clone with different ref."""
        url = "https://github.com/test/repo.git"
        target_path = Path("/tmp/repo")
        ref = "v1.0.0"
        
        git_clone(url, target_path, ref)
        
        mock_command.assert_called_once_with(["clone", url, str(target_path)])
        mock_checkout.assert_called_once_with(target_path, ref)


class TestGitBetterClone:
    @patch('rebuildr.tools.git.git_command')
    @patch('rebuildr.tools.git.git_checkout')
    def test_git_better_clone_new_repo(self, mock_checkout, mock_command):
        """Test git better clone for new repository."""
        url = "https://github.com/test/repo.git"
        target_path = Path("/tmp/repo")
        ref = "main"
        
        # Mock that .git doesn't exist
        with patch.object(Path, 'exists', return_value=False):
            with patch.object(Path, 'mkdir') as mock_mkdir:
                git_better_clone(url, target_path, ref)
        
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        
        expected_calls = [
            call(["init", str(target_path)]),
            call(["remote", "add", "origin", url], cwd=str(target_path)),
            call(["fetch", "origin", ref], cwd=str(target_path))
        ]
        mock_command.assert_has_calls(expected_calls)
        mock_checkout.assert_called_once_with(target_path, ref, force=True)

    @patch('rebuildr.tools.git.git_command')
    @patch('rebuildr.tools.git.git_checkout')
    def test_git_better_clone_existing_repo(self, mock_checkout, mock_command):
        """Test git better clone for existing repository."""
        url = "https://github.com/test/repo.git"
        target_path = Path("/tmp/repo")
        ref = "main"
        
        # Mock that .git exists
        with patch.object(Path, 'exists', return_value=True):
            git_better_clone(url, target_path, ref)
        
        # Should only call checkout, not init/fetch
        mock_command.assert_not_called()
        mock_checkout.assert_called_once_with(target_path, ref, force=True)

    @patch('rebuildr.tools.git.git_command')
    @patch('rebuildr.tools.git.git_checkout')
    def test_git_better_clone_nested_git_check(self, mock_checkout, mock_command):
        """Test git better clone checks for .git directory correctly."""
        url = "https://github.com/test/repo.git"
        target_path = Path("/tmp/repo")
        ref = "main"
        
        # Mock .git directory exists by patching Path.exists
        with patch.object(Path, 'exists') as mock_exists:
            mock_exists.return_value = True
            git_better_clone(url, target_path, ref)
        
        mock_command.assert_not_called()
        mock_checkout.assert_called_once_with(target_path, ref, force=True)


class TestGitCheckout:
    @patch('rebuildr.tools.git.git_command')
    def test_git_checkout_basic(self, mock_command):
        """Test basic git checkout functionality."""
        repo_path = Path("/tmp/repo")
        ref = "main"
        
        git_checkout(repo_path, ref)
        
        mock_command.assert_called_once_with(
            ["checkout", ref],
            cwd=str(repo_path)
        )

    @patch('rebuildr.tools.git.git_command')
    def test_git_checkout_with_force(self, mock_command):
        """Test git checkout with force flag."""
        repo_path = Path("/tmp/repo")
        ref = "main"
        
        git_checkout(repo_path, ref, force=True)
        
        mock_command.assert_called_once_with(
            ["checkout", "--force", ref],
            cwd=str(repo_path)
        )

    @patch('rebuildr.tools.git.git_command')
    def test_git_checkout_without_force(self, mock_command):
        """Test git checkout without force flag."""
        repo_path = Path("/tmp/repo")
        ref = "main"
        
        git_checkout(repo_path, ref, force=False)
        
        mock_command.assert_called_once_with(
            ["checkout", ref],
            cwd=str(repo_path)
        )

    @patch('rebuildr.tools.git.git_command')
    def test_git_checkout_different_refs(self, mock_command):
        """Test git checkout with different ref types."""
        repo_path = Path("/tmp/repo")
        
        # Test with branch
        git_checkout(repo_path, "feature-branch")
        mock_command.assert_called_with(
            ["checkout", "feature-branch"],
            cwd=str(repo_path)
        )
        
        # Test with tag
        git_checkout(repo_path, "v1.0.0")
        mock_command.assert_called_with(
            ["checkout", "v1.0.0"],
            cwd=str(repo_path)
        )
        
        # Test with commit hash
        git_checkout(repo_path, "abc123def456")
        mock_command.assert_called_with(
            ["checkout", "abc123def456"],
            cwd=str(repo_path)
        )


class TestGitLsRemote:
    @patch('rebuildr.tools.git.git_command')
    def test_git_ls_remote_basic(self, mock_command):
        """Test basic git ls-remote functionality."""
        url = "https://github.com/test/repo.git"
        ref = "main"
        
        # Mock successful command output
        mock_result = MagicMock()
        mock_result.stdout = "abc123def456\trefs/heads/main\n"
        mock_command.return_value = mock_result
        
        result = git_ls_remote(url, ref)
        
        mock_command.assert_called_once_with(
            ["ls-remote", "--heads", "--tags", url, ref],
            capture_output=True,
            text=True
        )
        assert result == "abc123def456"

    @patch('rebuildr.tools.git.git_command')
    def test_git_ls_remote_with_tag(self, mock_command):
        """Test git ls-remote with tag reference."""
        url = "https://github.com/test/repo.git"
        ref = "v1.0.0"
        
        # Mock successful command output
        mock_result = MagicMock()
        mock_result.stdout = "def456abc123\trefs/tags/v1.0.0\n"
        mock_command.return_value = mock_result
        
        result = git_ls_remote(url, ref)
        
        mock_command.assert_called_once_with(
            ["ls-remote", "--heads", "--tags", url, ref],
            capture_output=True,
            text=True
        )
        assert result == "def456abc123"

    @patch('rebuildr.tools.git.git_command')
    def test_git_ls_remote_multiple_output(self, mock_command):
        """Test git ls-remote with multiple matching refs."""
        url = "https://github.com/test/repo.git"
        ref = "main"
        
        # Mock command output with multiple refs
        mock_result = MagicMock()
        mock_result.stdout = """abc123def456\trefs/heads/main
def456abc123\trefs/heads/main-backup
ghi789jkl012\trefs/remotes/origin/main
"""
        mock_command.return_value = mock_result
        
        result = git_ls_remote(url, ref)
        
        # Should return the first hash
        assert result == "abc123def456"

    @patch('rebuildr.tools.git.git_command')
    def test_git_ls_remote_empty_output(self, mock_command):
        """Test git ls-remote with empty output."""
        url = "https://github.com/test/repo.git"
        ref = "nonexistent"
        
        # Mock empty command output
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_command.return_value = mock_result
        
        with pytest.raises(ValueError, match=f"Ref {ref} not found in {url}"):
            git_ls_remote(url, ref)

    @patch('rebuildr.tools.git.git_command')
    def test_git_ls_remote_whitespace_output(self, mock_command):
        """Test git ls-remote with whitespace-only output."""
        url = "https://github.com/test/repo.git"
        ref = "nonexistent"
        
        # Mock whitespace-only command output
        mock_result = MagicMock()
        mock_result.stdout = "   \n\t  \n"
        mock_command.return_value = mock_result
        
        with pytest.raises(ValueError, match=f"Ref {ref} not found in {url}"):
            git_ls_remote(url, ref)

    @patch('rebuildr.tools.git.git_command')
    def test_git_ls_remote_parse_hash_correctly(self, mock_command):
        """Test git ls-remote parses hash correctly from complex output."""
        url = "https://github.com/test/repo.git"
        ref = "main"
        
        # Mock command output with complex format
        mock_result = MagicMock()
        mock_result.stdout = """abc123def456789\trefs/heads/main\trefs/remotes/origin/main
def456abc123\trefs/tags/v1.0.0
"""
        mock_command.return_value = mock_result
        
        result = git_ls_remote(url, ref)
        
        # Should return the first hash (before first tab)
        assert result == "abc123def456789"


class TestDockerfileParametrized:
    def test_dockerfile_parametrized_basic(self):
        """Test basic dockerfile parametrization."""
        owner = "test-owner"
        repo = "test-repo"
        commit = "abc123def456"
        
        result = dockerfile_parametrized(owner, repo, commit)
        
        assert "FROM alpine/git@sha256:3ed9c9f02659076c2c1fe10de48a8851bc640b7133b3620a7be7a148e4a92715 as fetcher" in result
        assert f"git clone https://github.com/{owner}/{repo}.git . -b {commit} --single-branch" in result
        assert "FROM scratch" in result
        assert "COPY --from=fetcher /repo /" in result

    def test_dockerfile_parametrized_different_values(self):
        """Test dockerfile parametrization with different values."""
        owner = "microsoft"
        repo = "vscode"
        commit = "v1.80.0"
        
        result = dockerfile_parametrized(owner, repo, commit)
        
        assert f"git clone https://github.com/{owner}/{repo}.git . -b {commit} --single-branch" in result

    def test_dockerfile_parametrized_special_characters(self):
        """Test dockerfile parametrization with special characters."""
        owner = "test-owner_with-dash"
        repo = "test.repo.with.dots"
        commit = "feature/branch-name"
        
        result = dockerfile_parametrized(owner, repo, commit)
        
        assert f"git clone https://github.com/{owner}/{repo}.git . -b {commit} --single-branch" in result

    def test_dockerfile_parametrized_structure(self):
        """Test that dockerfile has correct structure."""
        owner = "test"
        repo = "test"
        commit = "main"
        
        result = dockerfile_parametrized(owner, repo, commit)
        
        lines = result.strip().split('\n')
        
        # Check that it starts with FROM
        assert lines[0].startswith("FROM alpine/git")
        assert "as fetcher" in lines[0]
        
        # Check WORKDIR
        assert "WORKDIR /repo" in lines
        
        # Check RUN command
        run_line = next(line for line in lines if line.startswith("RUN"))
        assert "git clone" in run_line
        assert "https://github.com/test/test.git" in run_line
        assert "-b main" in run_line
        assert "--single-branch" in run_line
        
        # Check second FROM
        assert "FROM scratch" in lines
        
        # Check COPY command
        assert "COPY --from=fetcher /repo /" in lines

    def test_dockerfile_parametrized_sha256_hash(self):
        """Test that dockerfile uses correct SHA256 hash."""
        owner = "test"
        repo = "test"
        commit = "main"
        
        result = dockerfile_parametrized(owner, repo, commit)
        
        expected_hash = "3ed9c9f02659076c2c1fe10de48a8851bc640b7133b3620a7be7a148e4a92715"
        assert f"alpine/git@sha256:{expected_hash}" in result