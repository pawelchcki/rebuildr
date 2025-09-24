import logging
from pathlib import Path, PurePath
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
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            # Preserve file modification and creation times
            shutil.copy2(src_path, dest_path)  # copy2 preserves metadata
        except (OSError, IOError) as e:
            raise RuntimeError(f"Failed to copy {src_path} to {dest_path}: {e}")

    def prepare_from_descriptor(self, descriptor: StableDescriptor):
        files_path = self.src_path()
        try:
            files_path.mkdir(parents=True, exist_ok=True)
        except (OSError, IOError) as e:
            raise RuntimeError(f"Failed to create files directory {files_path}: {e}")

        for file in descriptor.inputs.files:
            dest_path = files_path / file.target_path
            src_path = file.absolute_src_path
            LocalContext._copy_file(src_path, dest_path)

        for file in descriptor.inputs.builders:
            if isinstance(file, StableFileInput):
                dest_path = self.root_dir / file.target_path
                src_path = file.absolute_src_path
                LocalContext._copy_file(src_path, dest_path)
            elif isinstance(file, StableEnvInput):
                pass
            else:
                raise ValueError("Unknown input type")

        for external in descriptor.inputs.external:
            if isinstance(external, StableGitHubCommitInput):
                target_path = self.src_path() / external.target_path
                try:
                    target_path.mkdir(parents=True, exist_ok=True)
                except (OSError, IOError) as e:
                    raise RuntimeError(
                        f"Failed to create external directory {target_path}: {e}"
                    )
                # TODO: improve caching in remote builders
                # if not self.attempt_to_load_from_current_builder(
                #     external.commit, target_path
                # ):
                git_better_clone(external.url, target_path, external.commit)
            # self.store_in_docker_current_builder(external.commit, target_path)

            elif isinstance(external, StableGitRepoInput):
                target_path = self.src_path() / external.target_path
                try:
                    target_path.mkdir(parents=True, exist_ok=True)
                except (OSError, IOError) as e:
                    raise RuntimeError(
                        f"Failed to create external directory {target_path}: {e}"
                    )

                # if not self.attempt_to_load_from_current_builder(
                #     external.commit, target_path
                # ):
                git_better_clone(external.url, target_path, external.commit)
                # self.store_in_docker_current_builder(external.commit, target_path)

    def write_builders_file(self, path: str | PurePath, content: str):
        file_path = self.builders_path() / path
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, IOError) as e:
            raise RuntimeError(f"Failed to create builders directory for {path}: {e}")
        try:
            with open(file_path, "w") as f:
                f.write(content)
        except (OSError, IOError) as e:
            raise RuntimeError(f"Failed to write builders file {file_path}: {e}")
        return file_path

    def attempt_to_load_from_current_builder(self, ref_key, output_path: Path):
        tag = f"x1__internal_cachestore_{ref_key}"
        dockerfile_path = self.write_builders_file(
            "__internal_cachestore_read.Dockerfile",
            f"""FROM {tag} as cached""",
        )

        logging.debug(f"Attempting to load from {tag}")
        temp_dir = tempfile.TemporaryDirectory()
        try:
            DockerCLIBuilder(quiet=True, quiet_errors=True).build(
                root_dir=self.src_path(),
                dockerfile=dockerfile_path,
                output=f"type=local,dest={temp_dir.name}",
            )
        except RuntimeError:
            return False

        return True

    def store_in_docker_current_builder(self, ref_key, path: Path):
        tag = f"x1__internal_cachestore_{ref_key}"
        dockerfile_content = """
        FROM scratch as to_be_cached
        COPY / /"""
        dockerfile_path = self.write_builders_file(
            "__internal_cachestore.Dockerfile", dockerfile_content
        )

        logging.debug(f"Storing {path} in {tag}")
        DockerCLIBuilder(quiet=True).build(
            root_dir=path,
            dockerfile=dockerfile_path,
            # platform="linux/amd64",
            output=f"type=image,name={tag}",
        )
