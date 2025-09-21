from pathlib import Path
import shutil
import tarfile
import tempfile

from rebuildr.stable_descriptor import (
    StableDescriptor,
)


class TarContext(object):
    def __init__(self):
        self.temp_file = tempfile.NamedTemporaryFile()
        self.temp_file_path = Path(self.temp_file.name)
        self.tar = tarfile.open(self.temp_file_path, "w:")

    def __del__(self):
        """Clean up resources when object is destroyed"""
        if hasattr(self, "tar") and self.tar:
            try:
                self.tar.close()
            except Exception:
                pass
        if hasattr(self, "temp_file") and self.temp_file:
            try:
                self.temp_file.close()
            except Exception:
                pass

    def prepare_from_descriptor(self, descriptor: StableDescriptor):
        for file in descriptor.inputs.files:
            try:
                self.tar.add(file.absolute_src_path, arcname=file.path)
            except (OSError, IOError, tarfile.TarError) as e:
                raise RuntimeError(
                    f"Failed to add file {file.absolute_src_path} to tar: {e}"
                )

    def copy_to_file(self, path: Path):
        try:
            self.tar.close()
            shutil.copyfile(self.temp_file_path, path)
            # reopen file
            self.tar = tarfile.open(self.temp_file_path, "a:")
        except (OSError, IOError, tarfile.TarError) as e:
            raise RuntimeError(f"Failed to copy tar file to {path}: {e}")
