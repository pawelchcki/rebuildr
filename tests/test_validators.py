import pytest
from pathlib import PurePath

from rebuildr.validators import target_path_is_set, target_path_is_not_root


class TestTargetPathIsSet:
    def test_target_path_is_set_valid_string(self):
        """Test that valid string target paths pass validation."""
        # Should not raise any exception
        target_path_is_set("valid/path", str)
        target_path_is_set("single_file.txt", str)
        target_path_is_set("nested/path/to/file.txt", str)

    def test_target_path_is_set_valid_purepath(self):
        """Test that valid PurePath target paths pass validation."""
        # Should not raise any exception
        target_path_is_set(PurePath("valid/path"), PurePath)
        target_path_is_set(PurePath("single_file.txt"), PurePath)
        target_path_is_set(PurePath("nested/path/to/file.txt"), PurePath)

    def test_target_path_is_set_empty_string(self):
        """Test that empty string target paths raise ValueError."""
        with pytest.raises(ValueError, match="target_path must be set and not empty"):
            target_path_is_set("", str)

    def test_target_path_is_set_none(self):
        """Test that None target paths raise ValueError."""
        with pytest.raises(ValueError, match="target_path must be set and not empty"):
            target_path_is_set(None, str)

    def test_target_path_is_set_falsy_values(self):
        """Test that falsy values raise ValueError."""
        with pytest.raises(ValueError, match="target_path must be set and not empty"):
            target_path_is_set(0, int)
        
        with pytest.raises(ValueError, match="target_path must be set and not empty"):
            target_path_is_set(False, bool)

    def test_target_path_is_set_custom_class_name(self):
        """Test that custom class names are used in error messages."""
        class CustomClass:
            pass
        
        with pytest.raises(ValueError, match="CustomClass.target_path must be set and not empty"):
            target_path_is_set("", CustomClass)


class TestTargetPathIsNotRoot:
    def test_target_path_is_not_root_valid_paths(self):
        """Test that valid non-root paths pass validation."""
        # Should not raise any exception
        target_path_is_not_root("valid/path", str)
        target_path_is_not_root("single_file.txt", str)
        target_path_is_not_root("nested/path/to/file.txt", str)
        target_path_is_not_root("subdir/", str)
        
        target_path_is_not_root(PurePath("valid/path"), PurePath)
        target_path_is_not_root(PurePath("single_file.txt"), PurePath)
        target_path_is_not_root(PurePath("nested/path/to/file.txt"), PurePath)

    def test_target_path_is_not_root_current_directory_string(self):
        """Test that current directory (.) raises ValueError."""
        with pytest.raises(ValueError, match="target_path=\\. must not be the root directory"):
            target_path_is_not_root(".", str)

    def test_target_path_is_not_root_root_directory_string(self):
        """Test that root directory (/) raises ValueError."""
        with pytest.raises(ValueError, match="target_path=/ must not be the root directory"):
            target_path_is_not_root("/", str)

    def test_target_path_is_not_root_current_directory_purepath(self):
        """Test that current directory (.) PurePath raises ValueError."""
        with pytest.raises(ValueError, match="target_path=\\. must not be the root directory"):
            target_path_is_not_root(PurePath("."), PurePath)

    def test_target_path_is_not_root_root_directory_purepath(self):
        """Test that root directory (/) PurePath raises ValueError."""
        with pytest.raises(ValueError, match="target_path=/ must not be the root directory"):
            target_path_is_not_root(PurePath("/"), PurePath)

    def test_target_path_is_not_root_custom_class_name(self):
        """Test that custom class names are used in error messages."""
        class CustomClass:
            pass
        
        with pytest.raises(ValueError, match="CustomClass.target_path=\\. must not be the root directory"):
            target_path_is_not_root(".", CustomClass)

    def test_target_path_is_not_root_edge_cases(self):
        """Test edge cases for root directory detection."""
        # These should all be valid (not root)
        target_path_is_not_root("..", str)  # Parent directory
        target_path_is_not_root("...", str)  # Multiple dots
        target_path_is_not_root("./file", str)  # Relative path starting with ./
        target_path_is_not_root("/file", str)  # Absolute path to file
        
        # These should raise ValueError (are root)
        with pytest.raises(ValueError):
            target_path_is_not_root(".", str)
        
        with pytest.raises(ValueError):
            target_path_is_not_root("/", str)

    def test_target_path_is_not_root_whitespace(self):
        """Test that whitespace-only paths are treated as valid (not root)."""
        # Whitespace-only paths should not be considered root
        target_path_is_not_root(" ", str)
        target_path_is_not_root("  ", str)
        target_path_is_not_root("\t", str)
        target_path_is_not_root("\n", str)

    def test_target_path_is_not_root_empty_string(self):
        """Test that empty string is treated as root (should raise error)."""
        # Empty string should be considered root
        with pytest.raises(ValueError, match="must not be the root directory"):
            target_path_is_not_root("", str)

    def test_target_path_is_not_root_none(self):
        """Test that None raises appropriate error."""
        # None should raise an error when converted to PurePath
        with pytest.raises(TypeError):
            target_path_is_not_root(None, str)