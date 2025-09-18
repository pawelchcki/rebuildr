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

    def prepare_from_descriptor(self, descriptor: StableDescriptor):
        for file in descriptor.inputs.files:
            self.tar.add(file.absolute_src_path, arcname=file.target_path)

    def copy_to_file(self, path: Path):
        self.tar.close()
        shutil.copyfile(self.temp_file_path, path)
        # reopen file
        self.tar = tarfile.open(self.temp_file_path, "a:")
