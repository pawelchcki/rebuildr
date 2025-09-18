import pytest
import subprocess
import socket
import urllib.request
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from rebuildr.containers.docker import (
    is_docker_available,
    docker_bin,
    docker_image_exists_locally,
    docker_image_exists_in_registry,
    docker_pull_image,
    docker_push_image,
)
from rebuildr.containers.util import (
    image_exists_locally,
    image_exists_in_registry,
    pull_image,
    push_image,
)


class TestIsDockerAvailable:
    @patch('rebuildr.containers.docker.shutil.which')
    def test_is_docker_available_true(self, mock_which):
        """Test is_docker_available returns True when docker is found."""
        mock_which.return_value = "/usr/bin/docker"
        
        result = is_docker_available()
        
        mock_which.assert_called_once_with("docker")
        assert result is True

    @patch('rebuildr.containers.docker.shutil.which')
    def test_is_docker_available_false(self, mock_which):
        """Test is_docker_available returns False when docker is not found."""
        mock_which.return_value = None
        
        result = is_docker_available()
        
        mock_which.assert_called_once_with("docker")
        assert result is False


class TestDockerBin:
    @patch('rebuildr.containers.docker.shutil.which')
    def test_docker_bin_success(self, mock_which):
        """Test docker_bin returns path when docker is available."""
        mock_which.return_value = "/usr/bin/docker"
        
        result = docker_bin()
        
        # docker_bin() calls shutil.which("docker") twice - once in is_docker_available() and once directly
        assert mock_which.call_count == 2
        assert result == Path("/usr/bin/docker")

    @patch('rebuildr.containers.docker.shutil.which')
    def test_docker_bin_not_available(self, mock_which):
        """Test docker_bin raises ValueError when docker is not available."""
        mock_which.return_value = None
        
        with pytest.raises(ValueError, match="docker is not available"):
            docker_bin()


class TestDockerImageExistsLocally:
    @patch('rebuildr.containers.docker.docker_bin')
    @patch('rebuildr.containers.docker.subprocess.run')
    def test_docker_image_exists_locally_true(self, mock_run, mock_docker_bin):
        """Test docker_image_exists_locally returns True when image exists."""
        mock_docker_bin.return_value = Path("/usr/bin/docker")
        mock_run.return_value = MagicMock(returncode=0)
        
        result = docker_image_exists_locally("test-image:latest")
        
        mock_run.assert_called_once_with(
            ["/usr/bin/docker", "image", "inspect", "test-image:latest"],
            check=True,
            capture_output=True,
            text=True
        )
        assert result is True

    @patch('rebuildr.containers.docker.docker_bin')
    @patch('rebuildr.containers.docker.subprocess.run')
    def test_docker_image_exists_locally_false(self, mock_run, mock_docker_bin):
        """Test docker_image_exists_locally returns False when image doesn't exist."""
        mock_docker_bin.return_value = Path("/usr/bin/docker")
        mock_run.side_effect = subprocess.CalledProcessError(1, "docker")
        
        result = docker_image_exists_locally("nonexistent-image:latest")
        
        assert result is False

    @patch('rebuildr.containers.docker.docker_bin')
    @patch('rebuildr.containers.docker.subprocess.run')
    def test_docker_image_exists_locally_different_tags(self, mock_run, mock_docker_bin):
        """Test docker_image_exists_locally with different image tags."""
        mock_docker_bin.return_value = Path("/usr/bin/docker")
        mock_run.return_value = MagicMock(returncode=0)
        
        # Test with different tag formats
        test_cases = [
            "ubuntu:20.04",
            "nginx:latest",
            "redis:alpine",
            "postgres:13",
            "my-registry.com/image:tag"
        ]
        
        for image_tag in test_cases:
            docker_image_exists_locally(image_tag)
            mock_run.assert_called_with(
                ["/usr/bin/docker", "image", "inspect", image_tag],
                check=True,
                capture_output=True,
                text=True
            )


class TestDockerImageExistsInRegistry:
    @patch('rebuildr.containers.docker.docker_bin')
    @patch('rebuildr.containers.docker.subprocess.run')
    @patch('rebuildr.containers.docker.socket.gethostbyname')
    @patch('rebuildr.containers.docker.urllib.request.urlopen')
    def test_docker_image_exists_in_registry_true(self, mock_urlopen, mock_gethostbyname, 
                                                mock_run, mock_docker_bin):
        """Test docker_image_exists_in_registry returns True when image exists."""
        mock_docker_bin.return_value = Path("/usr/bin/docker")
        mock_gethostbyname.return_value = "192.168.1.1"
        mock_urlopen.return_value = MagicMock()
        mock_run.return_value = MagicMock(returncode=0)
        
        result = docker_image_exists_in_registry("registry.example.com/image:latest")
        
        mock_gethostbyname.assert_called_once_with("registry.example.com")
        mock_urlopen.assert_called_once_with("http://registry.example.com", timeout=1)
        mock_run.assert_called_once_with(
            ["/usr/bin/docker", "manifest", "inspect", "registry.example.com/image:latest"],
            check=True,
            capture_output=True,
            text=True,
            timeout=100
        )
        assert result is True

    @patch('rebuildr.containers.docker.docker_bin')
    @patch('rebuildr.containers.docker.subprocess.run')
    @patch('rebuildr.containers.docker.socket.gethostbyname')
    def test_docker_image_exists_in_registry_dns_failure(self, mock_gethostbyname, 
                                                        mock_run, mock_docker_bin):
        """Test docker_image_exists_in_registry returns False on DNS failure."""
        mock_docker_bin.return_value = Path("/usr/bin/docker")
        mock_gethostbyname.side_effect = socket.gaierror("Name or service not known")
        
        result = docker_image_exists_in_registry("nonexistent-registry.com/image:latest")
        
        mock_gethostbyname.assert_called_once_with("nonexistent-registry.com")
        mock_run.assert_not_called()
        assert result is False

    @patch('rebuildr.containers.docker.docker_bin')
    @patch('rebuildr.containers.docker.subprocess.run')
    @patch('rebuildr.containers.docker.socket.gethostbyname')
    @patch('rebuildr.containers.docker.urllib.request.urlopen')
    def test_docker_image_exists_in_registry_http_failure(self, mock_urlopen, mock_gethostbyname, 
                                                        mock_run, mock_docker_bin):
        """Test docker_image_exists_in_registry returns False on HTTP failure."""
        mock_docker_bin.return_value = Path("/usr/bin/docker")
        mock_gethostbyname.return_value = "192.168.1.1"
        mock_urlopen.side_effect = Exception("Connection failed")
        
        result = docker_image_exists_in_registry("registry.example.com/image:latest")
        
        mock_gethostbyname.assert_called_once_with("registry.example.com")
        mock_urlopen.assert_called_once_with("http://registry.example.com", timeout=1)
        mock_run.assert_not_called()
        assert result is False

    @patch('rebuildr.containers.docker.docker_bin')
    @patch('rebuildr.containers.docker.subprocess.run')
    def test_docker_image_exists_in_registry_no_dot_in_hostname(self, mock_run, mock_docker_bin):
        """Test docker_image_exists_in_registry skips DNS check for hostnames without dots."""
        mock_docker_bin.return_value = Path("/usr/bin/docker")
        mock_run.return_value = MagicMock(returncode=0)
        
        result = docker_image_exists_in_registry("localhost/image:latest")
        
        # Should skip DNS resolution and go directly to manifest inspect
        mock_run.assert_called_once_with(
            ["/usr/bin/docker", "manifest", "inspect", "localhost/image:latest"],
            check=True,
            capture_output=True,
            text=True,
            timeout=100
        )
        assert result is True

    @patch('rebuildr.containers.docker.docker_bin')
    @patch('rebuildr.containers.docker.subprocess.run')
    def test_docker_image_exists_in_registry_manifest_failure(self, mock_run, mock_docker_bin):
        """Test docker_image_exists_in_registry returns False on manifest inspect failure."""
        mock_docker_bin.return_value = Path("/usr/bin/docker")
        mock_run.side_effect = subprocess.CalledProcessError(1, "docker")
        
        result = docker_image_exists_in_registry("registry.example.com/image:latest")
        
        assert result is False

    @patch('rebuildr.containers.docker.docker_bin')
    @patch('rebuildr.containers.docker.subprocess.run')
    def test_docker_image_exists_in_registry_timeout(self, mock_run, mock_docker_bin):
        """Test docker_image_exists_in_registry returns False on timeout."""
        mock_docker_bin.return_value = Path("/usr/bin/docker")
        mock_run.side_effect = subprocess.TimeoutExpired("docker", 100)
        
        result = docker_image_exists_in_registry("registry.example.com/image:latest")
        
        assert result is False


class TestDockerPullImage:
    @patch('rebuildr.containers.docker.docker_bin')
    @patch('rebuildr.containers.docker.subprocess.run')
    def test_docker_pull_image_success(self, mock_run, mock_docker_bin):
        """Test docker_pull_image executes successfully."""
        mock_docker_bin.return_value = Path("/usr/bin/docker")
        mock_run.return_value = MagicMock(returncode=0)
        
        docker_pull_image("test-image:latest")
        
        mock_run.assert_called_once_with(
            ["/usr/bin/docker", "pull", "test-image:latest"],
            check=True
        )

    @patch('rebuildr.containers.docker.docker_bin')
    @patch('rebuildr.containers.docker.subprocess.run')
    def test_docker_pull_image_failure(self, mock_run, mock_docker_bin):
        """Test docker_pull_image raises exception on failure."""
        mock_docker_bin.return_value = Path("/usr/bin/docker")
        mock_run.side_effect = subprocess.CalledProcessError(1, "docker")
        
        with pytest.raises(subprocess.CalledProcessError):
            docker_pull_image("nonexistent-image:latest")


class TestDockerPushImage:
    @patch('rebuildr.containers.docker.docker_image_exists_in_registry')
    @patch('rebuildr.containers.docker.docker_bin')
    @patch('rebuildr.containers.docker.subprocess.run')
    def test_docker_push_image_success(self, mock_run, mock_docker_bin, mock_exists):
        """Test docker_push_image executes successfully."""
        mock_docker_bin.return_value = Path("/usr/bin/docker")
        mock_exists.return_value = False
        mock_run.return_value = MagicMock(returncode=0)
        
        docker_push_image("test-image:latest", overwrite_in_registry=False)
        
        mock_exists.assert_called_once_with("test-image:latest")
        mock_run.assert_called_once_with(
            ["/usr/bin/docker", "push", "test-image:latest"],
            check=True
        )

    @patch('rebuildr.containers.docker.docker_image_exists_in_registry')
    @patch('rebuildr.containers.docker.docker_bin')
    @patch('rebuildr.containers.docker.subprocess.run')
    def test_docker_push_image_already_exists_no_overwrite(self, mock_run, mock_docker_bin, mock_exists):
        """Test docker_push_image skips push when image already exists and overwrite is False."""
        mock_docker_bin.return_value = Path("/usr/bin/docker")
        mock_exists.return_value = True
        
        docker_push_image("test-image:latest", overwrite_in_registry=False)
        
        mock_exists.assert_called_once_with("test-image:latest")
        mock_run.assert_not_called()

    @patch('rebuildr.containers.docker.docker_image_exists_in_registry')
    @patch('rebuildr.containers.docker.docker_bin')
    @patch('rebuildr.containers.docker.subprocess.run')
    def test_docker_push_image_overwrite(self, mock_run, mock_docker_bin, mock_exists):
        """Test docker_push_image pushes even when image exists if overwrite is True."""
        mock_docker_bin.return_value = Path("/usr/bin/docker")
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0)
        
        docker_push_image("test-image:latest", overwrite_in_registry=True)
        
        mock_exists.assert_not_called()
        mock_run.assert_called_once_with(
            ["/usr/bin/docker", "push", "test-image:latest"],
            check=True
        )


class TestImageExistsLocally:
    @patch('rebuildr.containers.util.is_docker_available')
    @patch('rebuildr.containers.util.docker_image_exists_locally')
    def test_image_exists_locally_docker_available(self, mock_docker_exists, mock_docker_available):
        """Test image_exists_locally when docker is available."""
        mock_docker_available.return_value = True
        mock_docker_exists.return_value = True
        
        result = image_exists_locally("test-image:latest")
        
        mock_docker_available.assert_called_once()
        mock_docker_exists.assert_called_once_with("test-image:latest")
        assert result is True

    @patch('rebuildr.containers.util.is_docker_available')
    @patch('rebuildr.containers.util.docker_image_exists_locally')
    def test_image_exists_locally_docker_not_available(self, mock_docker_exists, mock_docker_available):
        """Test image_exists_locally when docker is not available."""
        mock_docker_available.return_value = False
        
        result = image_exists_locally("test-image:latest")
        
        mock_docker_available.assert_called_once()
        mock_docker_exists.assert_not_called()
        assert result is False


class TestImageExistsInRegistry:
    @patch('rebuildr.containers.util.is_docker_available')
    @patch('rebuildr.containers.util.docker_image_exists_in_registry')
    def test_image_exists_in_registry_docker_available(self, mock_docker_exists, mock_docker_available):
        """Test image_exists_in_registry when docker is available."""
        mock_docker_available.return_value = True
        mock_docker_exists.return_value = True
        
        result = image_exists_in_registry("test-image:latest")
        
        mock_docker_available.assert_called_once()
        mock_docker_exists.assert_called_once_with("test-image:latest")
        assert result is True

    @patch('rebuildr.containers.util.is_docker_available')
    @patch('rebuildr.containers.util.docker_image_exists_in_registry')
    def test_image_exists_in_registry_docker_not_available(self, mock_docker_exists, mock_docker_available):
        """Test image_exists_in_registry when docker is not available."""
        mock_docker_available.return_value = False
        
        result = image_exists_in_registry("test-image:latest")
        
        mock_docker_available.assert_called_once()
        mock_docker_exists.assert_not_called()
        assert result is False


class TestPullImage:
    @patch('rebuildr.containers.util.is_docker_available')
    @patch('rebuildr.containers.util.docker_pull_image')
    def test_pull_image_docker_available(self, mock_docker_pull, mock_docker_available):
        """Test pull_image when docker is available."""
        mock_docker_available.return_value = True
        
        pull_image("test-image:latest")
        
        mock_docker_available.assert_called_once()
        mock_docker_pull.assert_called_once_with("test-image:latest")

    @patch('rebuildr.containers.util.is_docker_available')
    @patch('rebuildr.containers.util.docker_pull_image')
    def test_pull_image_docker_not_available(self, mock_docker_pull, mock_docker_available):
        """Test pull_image when docker is not available."""
        mock_docker_available.return_value = False
        
        pull_image("test-image:latest")
        
        mock_docker_available.assert_called_once()
        mock_docker_pull.assert_not_called()


class TestPushImage:
    @patch('rebuildr.containers.util.is_docker_available')
    @patch('rebuildr.containers.util.docker_push_image')
    def test_push_image_docker_available(self, mock_docker_push, mock_docker_available):
        """Test push_image when docker is available."""
        mock_docker_available.return_value = True
        
        push_image("test-image:latest", overwrite_in_registry=True)
        
        mock_docker_available.assert_called_once()
        mock_docker_push.assert_called_once_with("test-image:latest", True)

    @patch('rebuildr.containers.util.is_docker_available')
    @patch('rebuildr.containers.util.docker_push_image')
    def test_push_image_docker_not_available(self, mock_docker_push, mock_docker_available):
        """Test push_image when docker is not available."""
        mock_docker_available.return_value = False
        
        push_image("test-image:latest", overwrite_in_registry=False)
        
        mock_docker_available.assert_called_once()
        mock_docker_push.assert_not_called()

    @patch('rebuildr.containers.util.is_docker_available')
    @patch('rebuildr.containers.util.docker_push_image')
    def test_push_image_default_overwrite(self, mock_docker_push, mock_docker_available):
        """Test push_image with default overwrite_in_registry value."""
        mock_docker_available.return_value = True
        
        push_image("test-image:latest")
        
        mock_docker_push.assert_called_once_with("test-image:latest", False)