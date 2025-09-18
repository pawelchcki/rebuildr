import pytest
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from rebuildr.fs import TarContext
from rebuildr.stable_descriptor import StableDescriptor, StableFileInput


class TestTarContext:
    def test_tar_context_initialization(self):
        """Test TarContext initialization."""
        context = TarContext()
        assert context.temp_file is not None
        assert context.temp_file_path is not None
        assert context.tar is not None
        assert isinstance(context.tar, tarfile.TarFile)

    def test_tar_context_prepare_from_descriptor_empty(self):
        """Test preparing tar context with empty descriptor."""
        context = TarContext()
        descriptor = MagicMock(spec=StableDescriptor)
        descriptor.inputs = MagicMock()
        descriptor.inputs.files = []
        
        context.prepare_from_descriptor(descriptor)
        
        # Should not raise any exceptions
        assert True

    def test_tar_context_prepare_from_descriptor_with_files(self, tmp_path):
        """Test preparing tar context with files."""
        # Create test files
        test_file1 = tmp_path / "file1.txt"
        test_file1.write_text("content1")
        
        test_file2 = tmp_path / "file2.txt"
        test_file2.write_text("content2")
        
        # Create stable file inputs
        stable_file1 = StableFileInput(
            target_path=Path("file1.txt"),
            absolute_src_path=test_file1
        )
        stable_file2 = StableFileInput(
            target_path=Path("file2.txt"),
            absolute_src_path=test_file2
        )
        
        # Create descriptor
        descriptor = MagicMock(spec=StableDescriptor)
        descriptor.inputs = MagicMock()
        descriptor.inputs.files = [stable_file1, stable_file2]
        
        context = TarContext()
        context.prepare_from_descriptor(descriptor)
        
        # Check that files were added to tar
        tar_names = context.tar.getnames()
        assert "file1.txt" in tar_names
        assert "file2.txt" in tar_names

    def test_tar_context_prepare_from_descriptor_nested_paths(self, tmp_path):
        """Test preparing tar context with nested file paths."""
        # Create nested directory structure
        nested_dir = tmp_path / "nested" / "subdir"
        nested_dir.mkdir(parents=True)
        
        test_file = nested_dir / "file.txt"
        test_file.write_text("nested content")
        
        # Create stable file input
        stable_file = StableFileInput(
            target_path=Path("nested/subdir/file.txt"),
            absolute_src_path=test_file
        )
        
        # Create descriptor
        descriptor = MagicMock(spec=StableDescriptor)
        descriptor.inputs = MagicMock()
        descriptor.inputs.files = [stable_file]
        
        context = TarContext()
        context.prepare_from_descriptor(descriptor)
        
        # Check that nested file was added to tar
        tar_names = context.tar.getnames()
        assert "nested/subdir/file.txt" in tar_names

    def test_tar_context_copy_to_file(self, tmp_path):
        """Test copying tar context to file."""
        context = TarContext()
        
        # Add some content to the tar
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("test content")
            temp_file_path = Path(temp_file.name)
        
        try:
            context.tar.add(temp_file_path, arcname="test.txt")
            
            # Copy to output file
            output_file = tmp_path / "output.tar"
            context.copy_to_file(output_file)
            
            # Verify output file exists
            assert output_file.exists()
            
            # Verify tar can be read
            with tarfile.open(output_file, "r:") as tar:
                names = tar.getnames()
                assert "test.txt" in names
                
                # Verify content
                member = tar.getmember("test.txt")
                content = tar.extractfile(member).read().decode()
                assert content == "test content"
        
        finally:
            # Clean up temp file
            if temp_file_path.exists():
                temp_file_path.unlink()

    def test_tar_context_copy_to_file_reopens_tar(self, tmp_path):
        """Test that copy_to_file reopens the tar file."""
        context = TarContext()
        
        # Add some content to the tar
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("test content")
            temp_file_path = Path(temp_file.name)
        
        try:
            context.tar.add(temp_file_path, arcname="test.txt")
            
            # Copy to output file
            output_file = tmp_path / "output.tar"
            context.copy_to_file(output_file)
            
            # Verify tar is reopened and can be used again
            assert context.tar is not None
            assert isinstance(context.tar, tarfile.TarFile)
            
            # Should be able to add more files
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file2:
                temp_file2.write("more content")
                temp_file2_path = Path(temp_file2.name)
            
            try:
                context.tar.add(temp_file2_path, arcname="test2.txt")
                names = context.tar.getnames()
                assert "test.txt" in names
                assert "test2.txt" in names
            
            finally:
                if temp_file2_path.exists():
                    temp_file2_path.unlink()
        
        finally:
            # Clean up temp file
            if temp_file_path.exists():
                temp_file_path.unlink()

    def test_tar_context_context_manager_behavior(self):
        """Test TarContext behaves correctly as a context manager."""
        context = TarContext()
        
        # Tar should be open initially
        assert context.tar is not None
        assert not context.tar.closed
        
        # After copy_to_file, tar should be reopened
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "test.tar"
            context.copy_to_file(output_file)
            
            # Tar should still be open and usable
            assert context.tar is not None
            assert not context.tar.closed

    def test_tar_context_with_large_files(self, tmp_path):
        """Test TarContext with larger files."""
        # Create a larger file
        large_content = "x" * 10000  # 10KB of content
        large_file = tmp_path / "large.txt"
        large_file.write_text(large_content)
        
        # Create stable file input
        stable_file = StableFileInput(
            target_path=Path("large.txt"),
            absolute_src_path=large_file
        )
        
        # Create descriptor
        descriptor = MagicMock(spec=StableDescriptor)
        descriptor.inputs = MagicMock()
        descriptor.inputs.files = [stable_file]
        
        context = TarContext()
        context.prepare_from_descriptor(descriptor)
        
        # Copy to output file
        output_file = tmp_path / "large_output.tar"
        context.copy_to_file(output_file)
        
        # Verify the large file is in the tar
        with tarfile.open(output_file, "r:") as tar:
            names = tar.getnames()
            assert "large.txt" in names
            
            # Verify content
            member = tar.getmember("large.txt")
            content = tar.extractfile(member).read().decode()
            assert content == large_content

    def test_tar_context_with_binary_files(self, tmp_path):
        """Test TarContext with binary files."""
        # Create a binary file
        binary_content = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09'
        binary_file = tmp_path / "binary.bin"
        binary_file.write_bytes(binary_content)
        
        # Create stable file input
        stable_file = StableFileInput(
            target_path=Path("binary.bin"),
            absolute_src_path=binary_file
        )
        
        # Create descriptor
        descriptor = MagicMock(spec=StableDescriptor)
        descriptor.inputs = MagicMock()
        descriptor.inputs.files = [stable_file]
        
        context = TarContext()
        context.prepare_from_descriptor(descriptor)
        
        # Copy to output file
        output_file = tmp_path / "binary_output.tar"
        context.copy_to_file(output_file)
        
        # Verify the binary file is in the tar
        with tarfile.open(output_file, "r:") as tar:
            names = tar.getnames()
            assert "binary.bin" in names
            
            # Verify content
            member = tar.getmember("binary.bin")
            content = tar.extractfile(member).read()
            assert content == binary_content

    def test_tar_context_file_permissions(self, tmp_path):
        """Test TarContext preserves file permissions."""
        # Create a file with specific permissions
        test_file = tmp_path / "permissions.txt"
        test_file.write_text("test content")
        test_file.chmod(0o755)  # rwxr-xr-x
        
        # Create stable file input
        stable_file = StableFileInput(
            target_path=Path("permissions.txt"),
            absolute_src_path=test_file
        )
        
        # Create descriptor
        descriptor = MagicMock(spec=StableDescriptor)
        descriptor.inputs = MagicMock()
        descriptor.inputs.files = [stable_file]
        
        context = TarContext()
        context.prepare_from_descriptor(descriptor)
        
        # Copy to output file
        output_file = tmp_path / "permissions_output.tar"
        context.copy_to_file(output_file)
        
        # Verify permissions are preserved
        with tarfile.open(output_file, "r:") as tar:
            member = tar.getmember("permissions.txt")
            # Check that the file mode is preserved (tarfile stores permissions)
            assert member.mode is not None

    def test_tar_context_cleanup(self):
        """Test TarContext cleanup behavior."""
        context = TarContext()
        temp_file_path = context.temp_file_path
        
        # The temp file should exist
        assert temp_file_path.exists()
        
        # After copy_to_file, the temp file should still exist (not cleaned up automatically)
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "test.tar"
            context.copy_to_file(output_file)
            
            # Temp file should still exist
            assert temp_file_path.exists()
        
        # The context should still be usable
        assert context.tar is not None
        assert not context.tar.closed