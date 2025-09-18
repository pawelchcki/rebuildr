import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from rebuildr.cli import (
    load_py_desc,
    load_and_parse,
    parse_and_print_py,
    parse_and_write_bazel_stable_metadata,
    parse_build_args,
    build_docker,
    build_tar,
    parse_cli_parse_py,
    parse_cli,
    print_usage,
)


class TestLoadPyDesc:
    def test_load_py_desc_success(self, tmp_path):
        """Test successful loading of a rebuildr descriptor file."""
        # Create a test rebuildr file
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs, FileInput, ImageTarget

image = Descriptor(
    inputs=Inputs(
        files=[FileInput(path="test.txt", target_path="test.txt")]
    ),
    targets=[ImageTarget(repository="test-repo", tag="latest", dockerfile="Dockerfile")]
)
""")
        
        # Create the referenced files
        (tmp_path / "test.txt").write_text("test content")
        (tmp_path / "Dockerfile").write_text("FROM alpine")
        
        desc = load_py_desc(rebuildr_file)
        assert desc is not None
        assert len(desc.inputs.files) == 1
        assert desc.inputs.files[0].target_path == Path("test.txt")

    def test_load_py_desc_file_not_found(self):
        """Test loading a non-existent rebuildr file."""
        with pytest.raises(FileNotFoundError):
            load_py_desc("nonexistent.rebuildr.py")

    def test_load_py_desc_invalid_syntax(self, tmp_path):
        """Test loading a rebuildr file with invalid Python syntax."""
        rebuildr_file = tmp_path / "invalid.rebuildr.py"
        rebuildr_file.write_text("invalid python syntax !!!")
        
        with pytest.raises(SyntaxError):
            load_py_desc(rebuildr_file)

    def test_load_py_desc_with_root_dir_override(self, tmp_path):
        """Test loading with REBUILDR_OVERRIDE_ROOT_DIR environment variable."""
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs

image = Descriptor(inputs=Inputs())
""")
        
        override_dir = tmp_path / "override"
        override_dir.mkdir()
        
        with patch.dict(os.environ, {"REBUILDR_OVERRIDE_ROOT_DIR": str(override_dir)}):
            desc = load_py_desc(rebuildr_file)
            assert desc is not None


class TestLoadAndParse:
    def test_load_and_parse_success(self, tmp_path):
        """Test successful loading and parsing."""
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs, FileInput, ImageTarget

image = Descriptor(
    inputs=Inputs(
        files=[FileInput(path="test.txt", target_path="test.txt")]
    ),
    targets=[ImageTarget(repository="test-repo", tag="latest")]
)
""")
        
        (tmp_path / "test.txt").write_text("test content")
        (tmp_path / "Dockerfile").write_text("FROM alpine")
        
        data, content_id_tag = load_and_parse(str(rebuildr_file), {"arg": "value"})
        
        assert "inputs" in data
        assert "sha256" in data
        assert content_id_tag is not None

    def test_load_and_parse_no_targets(self, tmp_path):
        """Test loading descriptor with no targets."""
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs

image = Descriptor(inputs=Inputs())
""")
        
        with pytest.raises(ValueError, match="Only one target is supported"):
            load_and_parse(str(rebuildr_file), {})

    def test_load_and_parse_multiple_targets(self, tmp_path):
        """Test loading descriptor with multiple targets."""
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget

image = Descriptor(
    inputs=Inputs(),
    targets=[
        ImageTarget(repository="test-repo1", tag="latest"),
        ImageTarget(repository="test-repo2", tag="latest")
    ]
)
""")
        
        (tmp_path / "Dockerfile").write_text("FROM alpine")
        
        with pytest.raises(ValueError, match="Only one target is supported"):
            load_and_parse(str(rebuildr_file), {})


class TestParseBuildArgs:
    def test_parse_build_args_success(self):
        """Test successful parsing of build arguments."""
        args = ["key1=value1", "key2=value2", "key3=value3"]
        result = parse_build_args(args)
        
        assert result == {"key1": "value1", "key2": "value2", "key3": "value3"}

    def test_parse_build_args_empty(self):
        """Test parsing empty build arguments."""
        result = parse_build_args([])
        assert result == {}

    def test_parse_build_args_no_equals(self):
        """Test parsing build arguments without equals sign."""
        args = ["invalid_arg"]
        result = parse_build_args(args)
        assert result == {}

    def test_parse_build_args_multiple_equals(self):
        """Test parsing build arguments with multiple equals signs."""
        args = ["key=value=with=equals"]
        result = parse_build_args(args)
        assert result == {"key": "value=with=equals"}


class TestParseAndPrintPy:
    def test_parse_and_print_py(self, tmp_path, capsys):
        """Test parsing and printing JSON output."""
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs, FileInput, ImageTarget

image = Descriptor(
    inputs=Inputs(
        files=[FileInput(path="test.txt", target_path="test.txt")]
    ),
    targets=[ImageTarget(repository="test-repo", tag="latest")]
)
""")
        
        (tmp_path / "test.txt").write_text("test content")
        (tmp_path / "Dockerfile").write_text("FROM alpine")
        
        parse_and_print_py(str(rebuildr_file), {"arg": "value"})
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        
        assert "inputs" in output
        assert "sha256" in output


class TestParseAndWriteBazelStableMetadata:
    def test_parse_and_write_bazel_stable_metadata(self, tmp_path):
        """Test writing bazel stable metadata files."""
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs, FileInput, ImageTarget

image = Descriptor(
    inputs=Inputs(
        files=[FileInput(path="test.txt", target_path="test.txt")]
    ),
    targets=[ImageTarget(repository="test-repo", tag="latest")]
)
""")
        
        (tmp_path / "test.txt").write_text("test content")
        (tmp_path / "Dockerfile").write_text("FROM alpine")
        
        metadata_file = tmp_path / "metadata.json"
        tag_file = tmp_path / "tag.txt"
        
        parse_and_write_bazel_stable_metadata(
            str(rebuildr_file), 
            {"arg": "value"}, 
            str(metadata_file), 
            str(tag_file)
        )
        
        assert metadata_file.exists()
        assert tag_file.exists()
        
        # Check metadata file content
        with open(metadata_file) as f:
            metadata = json.load(f)
            assert "inputs" in metadata
            assert "sha256" in metadata
        
        # Check tag file content
        with open(tag_file) as f:
            tag = f.read().strip()
            assert tag.startswith("test-repo:")


class TestBuildDocker:
    @patch('rebuildr.cli.image_exists_locally')
    @patch('rebuildr.cli.image_exists_in_registry')
    @patch('rebuildr.cli.pull_image')
    @patch('rebuildr.cli.LocalContext')
    @patch('rebuildr.cli.DockerCLIBuilder')
    def test_build_docker_image_exists_locally(self, mock_builder, mock_context, 
                                            mock_pull, mock_exists_registry, 
                                            mock_exists_local, tmp_path):
        """Test building docker when image already exists locally."""
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget

image = Descriptor(
    inputs=Inputs(),
    targets=[ImageTarget(repository="test-repo", tag="latest")]
)
""")
        
        (tmp_path / "Dockerfile").write_text("FROM alpine")
        
        mock_exists_local.return_value = True
        mock_exists_registry.return_value = False
        
        result = build_docker(str(rebuildr_file), {})
        
        assert result == "test-repo:src-id-test-hash"
        mock_exists_local.assert_called_once()
        mock_builder.assert_not_called()

    @patch('rebuildr.cli.image_exists_locally')
    @patch('rebuildr.cli.image_exists_in_registry')
    @patch('rebuildr.cli.pull_image')
    def test_build_docker_image_exists_in_registry(self, mock_pull, 
                                                 mock_exists_registry, 
                                                 mock_exists_local, tmp_path):
        """Test building docker when image exists in registry."""
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget

image = Descriptor(
    inputs=Inputs(),
    targets=[ImageTarget(repository="test-repo", tag="latest")]
)
""")
        
        (tmp_path / "Dockerfile").write_text("FROM alpine")
        
        mock_exists_local.return_value = False
        mock_exists_registry.return_value = True
        
        result = build_docker(str(rebuildr_file), {}, fetch_if_not_local=True)
        
        mock_pull.assert_called_once()
        assert result == "test-repo:src-id-test-hash"

    def test_build_docker_no_targets(self, tmp_path):
        """Test building docker with no targets."""
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs

image = Descriptor(inputs=Inputs())
""")
        
        (tmp_path / "Dockerfile").write_text("FROM alpine")
        
        with pytest.raises(ValueError, match="Only one target is supported"):
            build_docker(str(rebuildr_file), {})

    def test_build_docker_no_tags(self, tmp_path):
        """Test building docker with no tags specified."""
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget

image = Descriptor(
    inputs=Inputs(),
    targets=[ImageTarget(repository="test-repo", also_tag_with_content_id=False)]
)
""")
        
        (tmp_path / "Dockerfile").write_text("FROM alpine")
        
        with pytest.raises(ValueError, match="No tags specified"):
            build_docker(str(rebuildr_file), {})


class TestBuildTar:
    @patch('rebuildr.cli.TarContext')
    def test_build_tar_success(self, mock_tar_context, tmp_path):
        """Test successful tar building."""
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs, FileInput

image = Descriptor(
    inputs=Inputs(
        files=[FileInput(path="test.txt", target_path="test.txt")]
    )
)
""")
        
        (tmp_path / "test.txt").write_text("test content")
        
        mock_context = MagicMock()
        mock_tar_context.return_value = mock_context
        
        output_file = tmp_path / "output.tar"
        build_tar(str(rebuildr_file), str(output_file))
        
        mock_context.prepare_from_descriptor.assert_called_once()
        mock_context.copy_to_file.assert_called_once_with(output_file)


class TestParseCliParsePy:
    def test_parse_cli_parse_py_no_args(self, caplog):
        """Test CLI parsing with no arguments."""
        parse_cli_parse_py([])
        # The function should log an error message
        assert "Path to rebuildr file is required" in caplog.text

    def test_parse_cli_parse_py_with_build_args(self, tmp_path, capsys):
        """Test CLI parsing with build arguments."""
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs

image = Descriptor(inputs=Inputs())
""")
        
        (tmp_path / "Dockerfile").write_text("FROM alpine")
        
        args = [str(rebuildr_file), "arg1=value1", "arg2=value2"]
        parse_cli_parse_py(args)
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "inputs" in output

    def test_parse_cli_parse_py_bazel_stable_metadata(self, tmp_path):
        """Test CLI parsing with bazel-stable-metadata command."""
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs

image = Descriptor(inputs=Inputs())
""")
        
        (tmp_path / "Dockerfile").write_text("FROM alpine")
        
        metadata_file = tmp_path / "metadata.json"
        tag_file = tmp_path / "tag.txt"
        
        args = [str(rebuildr_file), "bazel-stable-metadata", str(metadata_file), str(tag_file)]
        parse_cli_parse_py(args)
        
        assert metadata_file.exists()
        assert tag_file.exists()

    def test_parse_cli_parse_py_materialize_image(self, tmp_path, capsys):
        """Test CLI parsing with materialize-image command."""
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs, ImageTarget

image = Descriptor(
    inputs=Inputs(),
    targets=[ImageTarget(repository="test-repo", tag="latest")]
)
""")
        
        with patch('rebuildr.cli.build_docker') as mock_build:
            mock_build.return_value = "test-repo:latest"
            
            args = [str(rebuildr_file), "materialize-image"]
            parse_cli_parse_py(args)
            
            captured = capsys.readouterr()
            assert "test-repo:latest" in captured.out

    def test_parse_cli_parse_py_build_tar(self, tmp_path):
        """Test CLI parsing with build-tar command."""
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs

image = Descriptor(inputs=Inputs())
""")
        
        output_file = tmp_path / "output.tar"
        
        with patch('rebuildr.cli.build_tar') as mock_build_tar:
            args = [str(rebuildr_file), "build-tar", str(output_file)]
            parse_cli_parse_py(args)
            
            mock_build_tar.assert_called_once_with(str(rebuildr_file), str(output_file))

    def test_parse_cli_parse_py_help(self, capsys):
        """Test CLI parsing with help command."""
        args = ["-h"]
        parse_cli_parse_py(args)
        
        captured = capsys.readouterr()
        assert "Usage: rebuildr <command> <args>" in captured.out

    def test_parse_cli_parse_py_unknown_command(self, capsys):
        """Test CLI parsing with unknown command."""
        args = ["unknown-command"]
        parse_cli_parse_py(args)
        
        captured = capsys.readouterr()
        assert "Unknown command: unknown-command" in captured.out


class TestParseCli:
    def test_parse_cli_no_args(self, capsys, caplog):
        """Test CLI parsing with no arguments."""
        with patch('sys.argv', ["rebuildr"]):
            parse_cli()
        captured = capsys.readouterr()
        assert "Usage: rebuildr <command> <args>" in captured.out
        assert "No arguments provided" in caplog.text

    def test_parse_cli_load_py(self, tmp_path):
        """Test CLI parsing with load-py command."""
        rebuildr_file = tmp_path / "test.rebuildr.py"
        rebuildr_file.write_text("""
from rebuildr.descriptor import Descriptor, Inputs

image = Descriptor(inputs=Inputs())
""")
        
        with patch('rebuildr.cli.parse_cli_parse_py') as mock_parse:
            args = ["load-py", str(rebuildr_file)]
            with patch('sys.argv', ["rebuildr"] + args):
                parse_cli()
            
            mock_parse.assert_called_once_with(args[1:])

    def test_parse_cli_unknown_command(self, capsys, caplog):
        """Test CLI parsing with unknown command."""
        with patch('sys.argv', ["rebuildr", "unknown-command"]):
            parse_cli()
        
        captured = capsys.readouterr()
        assert "Usage: rebuildr <command> <args>" in captured.out
        assert "Unknown command: unknown-command" in caplog.text


class TestPrintUsage:
    def test_print_usage(self, capsys):
        """Test printing usage information."""
        print_usage()
        captured = capsys.readouterr()
        
        assert "Usage: rebuildr <command> <args>" in captured.out
        assert "Commands:" in captured.out
        assert "load-py" in captured.out
        assert "build-tar" in captured.out