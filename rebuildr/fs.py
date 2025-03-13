from os import mkdir
from pathlib import Path, PurePath
import shutil
import tempfile

from rebuildr.stable_descriptor import StableEnvInput, StableFileInput, StableDescriptor


class Context(object):
    def __init__(self, root_dir):
        if isinstance(root_dir, tempfile.TemporaryDirectory):
            self.temp_dir = root_dir
            self.root_dir = Path(root_dir.name)
        else:
            self.root_dir = Path(root_dir)

    def temp():
        root_dir = tempfile.TemporaryDirectory()
        return Context(root_dir)

    def prepare_from_descriptor(self, descriptor: StableDescriptor):
        files_path = self.root_dir / "src"
        files_path.mkdir(parents=True, exist_ok=True)

        builders_path = self.root_dir

        for file in descriptor.inputs.files:
            dest_path = files_path / file.path
            src_path = file.absolute_path

            dest_dir = dest_path.parent
            dest_dir.mkdir(parents=True, exist_ok=True)

            shutil.copy(src_path, dest_path)

        for file in descriptor.inputs.builders:
            if isinstance(file, StableFileInput):
                dest_path = builders_path / file.path
                src_path = file.absolute_path

                dest_dir = dest_path.parent
                dest_dir.mkdir(parents=True, exist_ok=True)

                shutil.copy(src_path, dest_path)
            elif isinstance(file, StableEnvInput):
                pass
            else:
                raise ValueError("Unknown input type")
