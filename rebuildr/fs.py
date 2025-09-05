from os import mkdir
from pathlib import Path, PurePath
import shutil
import tarfile
import tempfile

from rebuildr.stable_descriptor import (
    StableEnvInput,
    StableFileInput,
    StableDescriptor,
    StableGitHubCommitInput,
)
from rebuildr.tools.git import git_clone


class TarContext(object):
    def __init__(self):
        self.temp_file = tempfile.NamedTemporaryFile()
        self.temp_file_path = Path(self.temp_file.name)
        self.tar = tarfile.open(self.temp_file_path, "w:")

    def prepare_from_descriptor(self, descriptor: StableDescriptor):
        for file in descriptor.inputs.files:
            self.tar.add(file.absolute_path, arcname=file.path)

    def copy_to_file(self, path: Path):
        self.tar.close()
        shutil.copyfile(self.temp_file_path, path)
        # reopen file
        self.tar = tarfile.open(self.temp_file_path, "a:")


class Context(object):
    def __init__(self, root_dir):
        if isinstance(root_dir, tempfile.TemporaryDirectory):
            self.temp_dir = root_dir
            self.root_dir = Path(root_dir.name)
        else:
            self.root_dir = Path(root_dir)

    @staticmethod
    def temp() -> "Context":
        root_dir = tempfile.TemporaryDirectory()
        return Context(root_dir)

    @staticmethod
    def from_path(path: Path) -> "Context":
        return Context(path)

    def src_path(self) -> Path:
        return self.root_dir / "src"

    def _copy_file(self, src_path: Path, dest_path: Path):
        dest_dir = dest_path.parent

        dest_dir.mkdir(parents=True, exist_ok=True)

        # Preserve file modification and creation times
        src_stat = src_path.stat()
        shutil.copy2(src_path, dest_path)  # copy2 preserves metadata

    def prepare_from_descriptor(self, descriptor: StableDescriptor):
        files_path = self.src_path()
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

        for external in descriptor.inputs.external:
            if isinstance(external, StableGitHubCommitInput):
                target_path = builders_path / external.target_path
                target_path.mkdir(parents=True, exist_ok=True)

                git_clone(external.url, target_path, external.commit)
