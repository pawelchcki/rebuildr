import logging
from pathlib import Path
import shutil
import tempfile

from rebuildr.build import DockerCLIBuilder
from rebuildr.stable_descriptor import (
    StableEnvInput,
    StableFileInput,
    StableDescriptor,
    StableGitHubCommitInput,
    StableGitRepoInput,
)
from rebuildr.tools.git import git_better_clone


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

    @staticmethod
    def _copy_file(src_path: Path, dest_path: Path):
        dest_dir = dest_path.parent
        if dest_dir.is_file():
            raise ValueError(
                f"Destination {dest_dir} is a file but should be a directory, check configured inputs"
            )

        logging.debug(f"Copying {src_path} to {dest_path}")
        dest_dir.mkdir(parents=True, exist_ok=True)
        # Preserve file modification and creation times
        shutil.copy2(src_path, dest_path)  # copy2 preserves metadata

    def prepare_from_descriptor(self, descriptor: StableDescriptor):
        files_path = self.src_path()
        files_path.mkdir(parents=True, exist_ok=True)

        builders_path = self.root_dir

        for file in descriptor.inputs.files:
            dest_path = files_path / file.target_path
            src_path = file.absolute_src_path
            LocalContext._copy_file(src_path, dest_path)

        for file in descriptor.inputs.builders:
            if isinstance(file, StableFileInput):
                dest_path = builders_path / file.target_path
                src_path = file.absolute_src_path
                LocalContext._copy_file(src_path, dest_path)
            elif isinstance(file, StableEnvInput):
                pass
            else:
                raise ValueError("Unknown input type")

        for external in descriptor.inputs.external:
            if isinstance(external, StableGitHubCommitInput):
                target_path = builders_path / external.target_path
                target_path.mkdir(parents=True, exist_ok=True)

                git_better_clone(external.url, target_path, external.commit)
                self.store_in_docker_current_builder(external.commit, target_path)
            elif isinstance(external, StableGitRepoInput):
                target_path = builders_path / external.target_path
                target_path.mkdir(parents=True, exist_ok=True)

                git_better_clone(external.url, target_path, external.commit)
                self.store_in_docker_current_builder(external.commit, target_path)

    def store_in_docker_current_builder(self, ref_key, path: Path):
        dockerfile_content = """
FROM scratch
COPY / /"""
        dockerfile_path = self.builders_path() / "__internal_cachestore.Dockerfile"
        self.builders_path().mkdir(parents=True, exist_ok=True)

        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)
        tag = f"x__internal_cachestore_{ref_key}"
        logging.debug(f"Storing {path} in {tag}")
        DockerCLIBuilder().build(
            root_dir=path,
            dockerfile=dockerfile_path,
            platform="linux/amd64",
            tags=[tag],
        )
