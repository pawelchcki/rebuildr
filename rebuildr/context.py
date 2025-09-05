from pathlib import Path
import shutil
import tempfile

from rebuildr.build import DockerCLIBuilder
from rebuildr.containers.docker import docker_bin
from rebuildr.stable_descriptor import (
    StableEnvInput,
    StableFileInput,
    StableDescriptor,
    StableGitHubCommitInput,
    StableGitRepoInput,
)
from rebuildr.tools.git import git_clone


class LocalContext(object):
    def __init__(self, root_dir):
        if isinstance(root_dir, tempfile.TemporaryDirectory):
            self.temp_dir = root_dir
            self.root_dir = Path(root_dir.name)
        else:
            self.root_dir = Path(root_dir)

    @staticmethod
    def temp() -> "LocalContext":
        root_dir = tempfile.TemporaryDirectory()
        return LocalContext(root_dir)

    @staticmethod
    def from_path(path: Path) -> "LocalContext":
        return LocalContext(path)

    def src_path(self) -> Path:
        return self.root_dir / "src"

    def builders_path(self) -> Path:
        return self.root_dir / "builders"

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

        # for external in descriptor.inputs.external:
        #     if isinstance(external, StableGitHubCommitInput):
        #         target_path = builders_path / external.target_path
        #         target_path.mkdir(parents=True, exist_ok=True)

        #         git_clone(external.url, target_path, external.commit)
        #     elif isinstance(external, StableGitRepoInput):
        #         target_path = builders_path / external.target_path
        #         target_path.mkdir(parents=True, exist_ok=True)

        #         git_clone(external.url, target_path, external.commit)

    def store_in_docker_current_builder(self, platforms, ref_key):
        dockerfile_content = f"""
FROM scratch
COPY / /
"""
        dockerfile_path = self.builders_path() / "Dockerfile"
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)

        DockerCLIBuilder().build(
            root_dir=self.src_path(),
            dockerfile=dockerfile_path,
            tags=[ref_key],
        )
