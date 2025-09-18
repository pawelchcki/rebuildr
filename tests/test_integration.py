import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from rebuildr.cli import load_py_desc, build_tar, parse_and_print_py
from rebuildr.context import LocalContext
from rebuildr.stable_descriptor import StableEnvironment
from rebuildr.descriptor import Descriptor, Inputs, FileInput, ImageTarget


class TestEndToEndWorkflows:
    def test_simple_rebuildr_workflow(self, tmp_path):
        """Test a simple rebuildr workflow from descriptor to tar."""
        # Create test files
        app_file = tmp_path / "app.py"
        app_file.write_text("print('Hello, World!')")
        
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM python:3.9\nCOPY app.py /app.py\nCMD python /app.py")
        
        # Create rebuildr descriptor file
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text(f"""
from rebuildr.descriptor import Descriptor, Inputs, FileInput, ImageTarget

image = Descriptor(
    inputs=Inputs(
        files=[
            FileInput(path="app.py", target_path="app.py")
        ],
        builders=[
            FileInput(path="Dockerfile", target_path="Dockerfile")
        ]
    ),
    targets=[
        ImageTarget(
            repository="test-app",
            tag="latest",
            dockerfile="Dockerfile"
        )
    ]
)
""")
        
        # Test loading descriptor
        descriptor = load_py_desc(rebuildr_file)
        assert descriptor is not None
        assert len(descriptor.inputs.files) == 1
        assert len(descriptor.inputs.builders) == 2  # Dockerfile from builders + target dockerfile
        assert len(descriptor.targets) == 1
        
        # Test context preparation
        context = LocalContext.temp()
        context.prepare_from_descriptor(descriptor)
        
        # Verify files were copied correctly
        assert (context.src_path() / "app.py").exists()
        assert (context.src_path() / "app.py").read_text() == "print('Hello, World!')"
        assert (context.root_dir / "Dockerfile").exists()
        assert (context.root_dir / "Dockerfile").read_text() == "FROM python:3.9\nCOPY app.py /app.py\nCMD python /app.py"
        
        # Test tar building
        output_tar = tmp_path / "output.tar"
        build_tar(str(rebuildr_file), str(output_tar))
        
        assert output_tar.exists()
        assert output_tar.stat().st_size > 0

    def test_rebuildr_with_environment_variables(self, tmp_path):
        """Test rebuildr workflow with environment variables."""
        # Create test files
        config_file = tmp_path / "config.py"
        config_file.write_text("""
import os
DEBUG = os.getenv('DEBUG', 'false')
PORT = os.getenv('PORT', '8080')
""")
        
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM python:3.9\nCOPY config.py /config.py")
        
        # Create rebuildr descriptor file
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text(f"""
from rebuildr.descriptor import Descriptor, Inputs, FileInput, EnvInput, ImageTarget

image = Descriptor(
    inputs=Inputs(
        files=[
            FileInput(path="config.py", target_path="config.py")
        ],
        builders=[
            FileInput(path="Dockerfile", target_path="Dockerfile"),
            EnvInput(key="DEBUG", default="false"),
            EnvInput(key="PORT", default="8080")
        ]
    ),
    targets=[
        ImageTarget(
            repository="test-app",
            tag="latest",
            dockerfile="Dockerfile"
        )
    ]
)
""")
        
        # Test with environment variables
        with patch.dict('os.environ', {'DEBUG': 'true', 'PORT': '9000'}):
            descriptor = load_py_desc(rebuildr_file)
            env = StableEnvironment.from_os_env()
            
            # Test stable inputs dict
            stable_dict = descriptor.stable_inputs_dict(env)
            
            assert stable_dict["inputs"]["envs"][0]["key"] == "DEBUG"
            assert stable_dict["inputs"]["envs"][0]["value"] == "true"
            assert stable_dict["inputs"]["envs"][1]["key"] == "PORT"
            assert stable_dict["inputs"]["envs"][1]["value"] == "9000"
            
            # Test SHA calculation
            sha = descriptor.sha_sum(env)
            assert isinstance(sha, str)
            assert len(sha) == 64

    def test_rebuildr_with_build_arguments(self, tmp_path):
        """Test rebuildr workflow with build arguments."""
        # Create test files
        app_file = tmp_path / "app.py"
        app_file.write_text("print('Hello, World!')")
        
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM python:3.9\nARG VERSION\nCOPY app.py /app.py")
        
        # Create rebuildr descriptor file
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text(f"""
from rebuildr.descriptor import Descriptor, Inputs, FileInput, ArgsInput, ImageTarget

image = Descriptor(
    inputs=Inputs(
        files=[
            FileInput(path="app.py", target_path="app.py")
        ],
        builders=[
            FileInput(path="Dockerfile", target_path="Dockerfile"),
            ArgsInput(key="VERSION", default="1.0.0")
        ]
    ),
    targets=[
        ImageTarget(
            repository="test-app",
            tag="latest",
            dockerfile="Dockerfile"
        )
    ]
)
""")
        
        # Test with build arguments
        descriptor = load_py_desc(rebuildr_file)
        env = StableEnvironment.from_os_env({"VERSION": "2.0.0"})
        
        # Test stable inputs dict
        stable_dict = descriptor.stable_inputs_dict(env)
        
        assert stable_dict["inputs"]["build_args"][0]["key"] == "VERSION"
        assert stable_dict["inputs"]["build_args"][0]["value"] == "2.0.0"
        
        # Test SHA calculation
        sha = descriptor.sha_sum(env)
        assert isinstance(sha, str)
        assert len(sha) == 64

    def test_rebuildr_with_glob_patterns(self, tmp_path):
        """Test rebuildr workflow with glob patterns."""
        # Create multiple files matching pattern
        for i in range(3):
            file_path = tmp_path / f"file{i}.txt"
            file_path.write_text(f"content {i}")
        
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM alpine\nCOPY *.txt /files/")
        
        # Create rebuildr descriptor file
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text(f"""
from rebuildr.descriptor import Descriptor, Inputs, GlobInput, FileInput, ImageTarget

image = Descriptor(
    inputs=Inputs(
        files=[
            GlobInput(pattern="file*.txt", target_path="files")
        ],
        builders=[
            FileInput(path="Dockerfile", target_path="Dockerfile")
        ]
    ),
    targets=[
        ImageTarget(
            repository="test-app",
            tag="latest",
            dockerfile="Dockerfile"
        )
    ]
)
""")
        
        # Test loading descriptor
        descriptor = load_py_desc(rebuildr_file)
        
        # Test context preparation
        context = LocalContext.temp()
        context.prepare_from_descriptor(descriptor)
        
        # Verify all files were copied
        files_dir = context.src_path() / "files"
        assert files_dir.exists()
        
        copied_files = list(files_dir.glob("*.txt"))
        assert len(copied_files) == 3
        
        for i, file_path in enumerate(sorted(copied_files)):
            assert file_path.read_text() == f"content {i}"

    def test_rebuildr_with_nested_directories(self, tmp_path):
        """Test rebuildr workflow with nested directory structure."""
        # Create nested directory structure
        nested_dir = tmp_path / "src" / "app" / "modules"
        nested_dir.mkdir(parents=True)
        
        main_file = tmp_path / "src" / "main.py"
        main_file.write_text("import modules.utils")
        
        utils_file = nested_dir / "utils.py"
        utils_file.write_text("def helper(): pass")
        
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM python:3.9\nCOPY src/ /app/")
        
        # Create rebuildr descriptor file
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text(f"""
from rebuildr.descriptor import Descriptor, Inputs, FileInput, ImageTarget

image = Descriptor(
    inputs=Inputs(
        files=[
            FileInput(path="src/main.py", target_path="src/main.py"),
            FileInput(path="src/app/modules/utils.py", target_path="src/app/modules/utils.py")
        ],
        builders=[
            FileInput(path="Dockerfile", target_path="Dockerfile")
        ]
    ),
    targets=[
        ImageTarget(
            repository="test-app",
            tag="latest",
            dockerfile="Dockerfile"
        )
    ]
)
""")
        
        # Test loading descriptor
        descriptor = load_py_desc(rebuildr_file)
        
        # Test context preparation
        context = LocalContext.temp()
        context.prepare_from_descriptor(descriptor)
        
        # Verify nested structure was preserved
        assert (context.src_path() / "src" / "main.py").exists()
        assert (context.src_path() / "src" / "app" / "modules" / "utils.py").exists()
        
        assert (context.src_path() / "src" / "main.py").read_text() == "import modules.utils"
        assert (context.src_path() / "src" / "app" / "modules" / "utils.py").read_text() == "def helper(): pass"

    def test_rebuildr_with_binary_files(self, tmp_path):
        """Test rebuildr workflow with binary files."""
        # Create binary file
        binary_file = tmp_path / "data.bin"
        binary_content = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09'
        binary_file.write_bytes(binary_content)
        
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM alpine\nCOPY data.bin /data.bin")
        
        # Create rebuildr descriptor file
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text(f"""
from rebuildr.descriptor import Descriptor, Inputs, FileInput, ImageTarget

image = Descriptor(
    inputs=Inputs(
        files=[
            FileInput(path="data.bin", target_path="data.bin")
        ],
        builders=[
            FileInput(path="Dockerfile", target_path="Dockerfile")
        ]
    ),
    targets=[
        ImageTarget(
            repository="test-app",
            tag="latest",
            dockerfile="Dockerfile"
        )
    ]
)
""")
        
        # Test loading descriptor
        descriptor = load_py_desc(rebuildr_file)
        
        # Test context preparation
        context = LocalContext.temp()
        context.prepare_from_descriptor(descriptor)
        
        # Verify binary file was copied correctly
        copied_binary = context.src_path() / "data.bin"
        assert copied_binary.exists()
        assert copied_binary.read_bytes() == binary_content

    def test_rebuildr_cli_json_output(self, tmp_path, capsys):
        """Test rebuildr CLI JSON output."""
        # Create test files
        app_file = tmp_path / "app.py"
        app_file.write_text("print('Hello, World!')")
        
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM python:3.9\nCOPY app.py /app.py")
        
        # Create rebuildr descriptor file
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text(f"""
from rebuildr.descriptor import Descriptor, Inputs, FileInput, ImageTarget

image = Descriptor(
    inputs=Inputs(
        files=[
            FileInput(path="app.py", target_path="app.py")
        ],
        builders=[
            FileInput(path="Dockerfile", target_path="Dockerfile")
        ]
    ),
    targets=[
        ImageTarget(
            repository="test-app",
            tag="latest",
            dockerfile="Dockerfile"
        )
    ]
)
""")
        
        # Test CLI JSON output
        parse_and_print_py(str(rebuildr_file), {})
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        
        assert "inputs" in output
        assert "sha256" in output
        assert output["inputs"]["files"][0]["target_path"] == "app.py"
        assert output["inputs"]["builders"][0]["target_path"] == "Dockerfile"

    def test_rebuildr_multiple_targets(self, tmp_path):
        """Test rebuildr workflow with multiple targets."""
        # Create test files
        app_file = tmp_path / "app.py"
        app_file.write_text("print('Hello, World!')")
        
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM python:3.9\nCOPY app.py /app.py")
        
        # Create rebuildr descriptor file
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text(f"""
from rebuildr.descriptor import Descriptor, Inputs, FileInput, ImageTarget

image = Descriptor(
    inputs=Inputs(
        files=[
            FileInput(path="app.py", target_path="app.py")
        ],
        builders=[
            FileInput(path="Dockerfile", target_path="Dockerfile")
        ]
    ),
    targets=[
        ImageTarget(
            repository="test-app",
            tag="latest",
            dockerfile="Dockerfile"
        ),
        ImageTarget(
            repository="test-app",
            tag="v1.0.0",
            dockerfile="Dockerfile"
        )
    ]
)
""")
        
        # Test loading descriptor
        descriptor = load_py_desc(rebuildr_file)
        assert len(descriptor.targets) == 2
        
        # Test context preparation
        context = LocalContext.temp()
        context.prepare_from_descriptor(descriptor)
        
        # Verify files were copied
        assert (context.src_path() / "app.py").exists()
        assert (context.root_dir / "Dockerfile").exists()

    def test_rebuildr_with_platform_specific_targets(self, tmp_path):
        """Test rebuildr workflow with platform-specific targets."""
        # Create test files
        app_file = tmp_path / "app.py"
        app_file.write_text("print('Hello, World!')")
        
        dockerfile = tmp_path / "Dockerfile"
        dockerfile.write_text("FROM python:3.9\nCOPY app.py /app.py")
        
        # Create rebuildr descriptor file
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text(f"""
from rebuildr.descriptor import Descriptor, Inputs, FileInput, ImageTarget, Platform

image = Descriptor(
    inputs=Inputs(
        files=[
            FileInput(path="app.py", target_path="app.py")
        ],
        builders=[
            FileInput(path="Dockerfile", target_path="Dockerfile")
        ]
    ),
    targets=[
        ImageTarget(
            repository="test-app",
            tag="latest",
            dockerfile="Dockerfile",
            platform=Platform.LINUX_AMD64
        ),
        ImageTarget(
            repository="test-app",
            tag="latest-arm64",
            dockerfile="Dockerfile",
            platform=Platform.LINUX_ARM64
        )
    ]
)
""")
        
        # Test loading descriptor
        descriptor = load_py_desc(rebuildr_file)
        assert len(descriptor.targets) == 2
        
        # Test platform-specific content ID tags
        env = StableEnvironment.from_os_env()
        
        target1 = descriptor.targets[0]
        target2 = descriptor.targets[1]
        
        content_id1 = target1.content_id_tag(descriptor.inputs, env)
        content_id2 = target2.content_id_tag(descriptor.inputs, env)
        
        assert "linux-amd64-src-id-" in content_id1
        assert "linux-arm64-src-id-" in content_id2
        assert content_id1 != content_id2  # Different platforms should have different content IDs

    def test_rebuildr_with_complex_file_structure(self, tmp_path):
        """Test rebuildr workflow with complex file structure."""
        # Create complex file structure
        structure = [
            "src/main.py",
            "src/utils/helper.py",
            "src/utils/__init__.py",
            "config/app.conf",
            "data/sample.json",
            "docs/README.md",
            "tests/test_main.py",
            "Dockerfile",
            ".gitignore",
            "requirements.txt"
        ]
        
        for file_path in structure:
            full_path = tmp_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            if file_path.endswith('.py'):
                full_path.write_text(f"# {file_path}")
            elif file_path.endswith('.json'):
                full_path.write_text('{"test": "data"}')
            elif file_path.endswith('.md'):
                full_path.write_text(f"# {file_path}")
            elif file_path == 'Dockerfile':
                full_path.write_text("FROM python:3.9\nCOPY . /app/")
            elif file_path == '.gitignore':
                full_path.write_text("__pycache__/\n*.pyc")
            elif file_path == 'requirements.txt':
                full_path.write_text("flask==2.0.1")
            else:
                full_path.write_text(f"content for {file_path}")
        
        # Create rebuildr descriptor file
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text(f"""
from rebuildr.descriptor import Descriptor, Inputs, FileInput, ImageTarget

image = Descriptor(
    inputs=Inputs(
        files=[
            FileInput(path="src/main.py", target_path="src/main.py"),
            FileInput(path="src/utils/helper.py", target_path="src/utils/helper.py"),
            FileInput(path="src/utils/__init__.py", target_path="src/utils/__init__.py"),
            FileInput(path="config/app.conf", target_path="config/app.conf"),
            FileInput(path="data/sample.json", target_path="data/sample.json"),
            FileInput(path="docs/README.md", target_path="docs/README.md"),
            FileInput(path="tests/test_main.py", target_path="tests/test_main.py"),
            FileInput(path=".gitignore", target_path=".gitignore"),
            FileInput(path="requirements.txt", target_path="requirements.txt")
        ],
        builders=[
            FileInput(path="Dockerfile", target_path="Dockerfile")
        ]
    ),
    targets=[
        ImageTarget(
            repository="complex-app",
            tag="latest",
            dockerfile="Dockerfile"
        )
    ]
)
""")
        
        # Test loading descriptor
        descriptor = load_py_desc(rebuildr_file)
        
        # Test context preparation
        context = LocalContext.temp()
        context.prepare_from_descriptor(descriptor)
        
        # Verify all files were copied with correct structure
        for file_path in structure:
            if file_path == 'Dockerfile':
                assert (context.root_dir / file_path).exists()
            else:
                assert (context.src_path() / file_path).exists()
        
        # Verify content
        assert (context.src_path() / "src/main.py").read_text() == "# src/main.py"
        assert (context.src_path() / "data/sample.json").read_text() == '{"test": "data"}'
        assert (context.root_dir / "Dockerfile").read_text() == "FROM python:3.9\nCOPY . /app/"

    def test_rebuildr_error_handling_missing_file(self, tmp_path):
        """Test rebuildr error handling with missing files."""
        # Create rebuildr descriptor file referencing non-existent file
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text(f"""
from rebuildr.descriptor import Descriptor, Inputs, FileInput, ImageTarget

image = Descriptor(
    inputs=Inputs(
        files=[
            FileInput(path="nonexistent.py", target_path="nonexistent.py")
        ],
        builders=[
            FileInput(path="Dockerfile", target_path="Dockerfile")
        ]
    ),
    targets=[
        ImageTarget(
            repository="test-app",
            tag="latest",
            dockerfile="Dockerfile"
        )
    ]
)
""")
        
        # Test loading descriptor (should succeed)
        descriptor = load_py_desc(rebuildr_file)
        
        # Test context preparation (should fail)
        context = LocalContext.temp()
        with pytest.raises(FileNotFoundError):
            context.prepare_from_descriptor(descriptor)

    def test_rebuildr_error_handling_missing_dockerfile(self, tmp_path):
        """Test rebuildr error handling with missing Dockerfile."""
        # Create test files
        app_file = tmp_path / "app.py"
        app_file.write_text("print('Hello, World!')")
        
        # Create rebuildr descriptor file referencing non-existent Dockerfile
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text(f"""
from rebuildr.descriptor import Descriptor, Inputs, FileInput, ImageTarget

image = Descriptor(
    inputs=Inputs(
        files=[
            FileInput(path="app.py", target_path="app.py")
        ],
        builders=[]
    ),
    targets=[
        ImageTarget(
            repository="test-app",
            tag="latest",
            dockerfile="nonexistent.Dockerfile"
        )
    ]
)
""")
        
        # Test loading descriptor (should fail)
        with pytest.raises(ValueError, match="Dockerfile .* does not exist"):
            load_py_desc(rebuildr_file)