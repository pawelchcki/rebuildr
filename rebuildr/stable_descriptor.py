from dataclasses import asdict, dataclass, field
import glob
import hashlib
import json
import os
from pathlib import Path, PurePath
from typing import Optional, Self

from rebuildr.tools.git import git_ls_remote
from rebuildr.descriptor import (
    Descriptor,
    EnvInput,
    FileInput,
    GlobInput,
    ImageTarget,
    GitHubCommitInput,
    GitRepoInput,
    Platform,
)


class BaseInput:
    # used for sorting inputs to make the output stable
    def sort_key(self) -> str:
        raise NotImplementedError

    # used for hashing inputs
    def hash_update(self, hasher):
        raise NotImplementedError


@dataclass()
class StableEnvInput(BaseInput):
    key: str
    default: Optional[str] = None

    def sort_key(self) -> str:
        return self.key

    def hash_update(self, hasher):
        hasher.update(self.key.encode())
        value = os.environ.get(self.key)
        if value:
            hasher.update(value.encode())
        elif self.default:
            hasher.update(self.default.encode())


@dataclass
class StableGitHubCommitInput(BaseInput):
    url: str
    commit: str
    target_path: str | PurePath

    def sort_key(self) -> str:
        return self.commit

    def hash_update(self, hasher):
        hasher.update(self.commit.encode())


@dataclass
class StableGitRepoInput(BaseInput):
    url: str
    commit: str
    target_path: str | PurePath

    def sort_key(self) -> str:
        return self.commit

    def hash_update(self, hasher):
        hasher.update(self.commit.encode())


@dataclass
class StableFileInput:
    path: PurePath
    absolute_path: Path

    def sort_key(self) -> str:
        return str(self.path)

    def read_bytes(self) -> bytes:
        with open(self.absolute_path, "rb") as f:
            return f.read()

    def hash_update(self, hasher):
        hasher.update(self.read_bytes())


@dataclass
class StableInputs:
    envs: list[StableEnvInput]
    files: list[StableFileInput] = field(default_factory=list)
    builders: list[StableFileInput] = field(default_factory=list)
    external: list[StableGitHubCommitInput | StableGitRepoInput] = field(
        default_factory=list
    )

    def sha_sum(self):
        m = hashlib.sha256()
        for env_dep in sorted(self.envs, key=lambda x: x.sort_key()):
            env_dep.hash_update(m)

        # sort and iterate - order must be predictable - always
        for builder_dep in sorted(self.builders, key=lambda x: x.sort_key()):
            builder_dep.hash_update(m)

        for file_dep in sorted(self.files, key=lambda x: x.sort_key()):
            file_dep.hash_update(m)

        for external_dep in sorted(self.external, key=lambda x: x.sort_key()):
            external_dep.hash_update(m)

        return m.hexdigest()

    def find_file(self, path: PurePath) -> Optional[StableFileInput]:
        for file_dep in self.files:
            if file_dep.path == path:
                return file_dep

        for file_dep in self.builders:
            if file_dep.path == path:
                return file_dep

        return None


@dataclass
class StableImageTarget:
    repository: str
    dockerfile: PurePath
    tag: Optional[str] = None
    dockerfile_absolute_path: Optional[Path] = None
    also_tag_with_content_id: bool = True
    target: Optional[str] = None
    platform: Optional[Platform] = None

    def image_tags(self, inputs: StableInputs) -> list[str]:
        tags = []
        if self.tag:
            tags.append(self.repository + ":" + self.tag)
        if self.also_tag_with_content_id:
            tags.append(self.content_id_tag(inputs))

        return tags

    def content_id_tag(self, inputs: StableInputs) -> str:
        if self.platform is None:
            return f"{self.repository}:src-id-{inputs.sha_sum()}"
        else:
            platform_prefix = self.platform.value.replace("/", "-")
            return f"{self.repository}:{platform_prefix}-src-id-{inputs.sha_sum()}"


@dataclass(frozen=True)
class StableDescriptor:
    absolute_path: Path
    inputs: StableInputs
    targets: Optional[list[StableImageTarget]] = None

    def sha_sum(self):
        return self.inputs.sha_sum()

    def stable_inputs_dict(self):
        data = asdict(self.inputs)

        # Remove null values and absolute_path keys recursively
        def clean_dict(d):
            if isinstance(d, list):
                return [clean_dict(item) for item in d]
            if not isinstance(d, dict):
                return str(d)
            return {
                k: clean_dict(v)
                for k, v in d.items()
                if v is not None and k != "absolute_path"
            }

        return {
            "inputs": clean_dict(asdict(self.inputs)),
            "sha256": self.sha_sum(),
        }

    @staticmethod
    def _make_stable_files(files, root_dir: Path) -> list[StableFileInput]:
        stable_files = []
        for file_dep in files:
            if isinstance(file_dep, FileInput):
                stable_files.append(
                    StableFileInput(
                        path=PurePath(file_dep.path),
                        absolute_path=root_dir / file_dep.path,
                    )
                )
            elif isinstance(file_dep, GlobInput):
                glob_root = (
                    root_dir
                    if file_dep.root_dir is None
                    else root_dir / file_dep.root_dir
                )
                for path in glob.glob(
                    file_dep.pattern,
                    root_dir=glob_root,
                    recursive=True,
                    include_hidden=True,
                ):
                    path = PurePath(path)
                    absolute_path = glob_root / path
                    if not absolute_path.exists():
                        raise ValueError(f"File {absolute_path} does not exist")

                    if absolute_path.is_file():
                        stable_files.append(
                            StableFileInput(path=path, absolute_path=absolute_path)
                        )
            elif isinstance(file_dep, str):
                stable_files.append(
                    StableFileInput(
                        path=PurePath(file_dep),
                        absolute_path=root_dir / PurePath(file_dep),
                    )
                )
            else:
                raise ValueError(f"Unexpected input type {type(file_dep)}")
        stable_files.sort(key=lambda x: x.sort_key())
        return stable_files

    @staticmethod
    def from_descriptor(
        descriptor: Descriptor, absolute_path: Path
    ) -> "StableDescriptor":
        if not absolute_path.is_absolute():
            raise ValueError("absolute_path must be absolute")
        file_deps = StableDescriptor._make_stable_files(
            descriptor.inputs.files, absolute_path
        )

        env_deps = [
            StableEnvInput(key=dep.key, default=dep.default)
            for dep in descriptor.inputs.builders
            if isinstance(dep, EnvInput)
        ]
        # todo metadata from chosen target (like context build targets must be included in the sha sum of the tool)
        metadata_deps = []

        external_deps = []
        for dep in descriptor.inputs.external:
            if isinstance(dep, str):
                raise ValueError(
                    f"str definition of external dependency is not yet supported"
                )
            elif isinstance(dep, GitHubCommitInput):
                external_deps.append(
                    StableGitHubCommitInput(
                        url=f"https://github.com/{dep.owner}/{dep.repo}.git",
                        commit=dep.commit,
                        target_path=dep.target_path,
                    )
                )
            elif isinstance(dep, GitRepoInput):
                external_deps.append(
                    StableGitRepoInput(
                        url=dep.url,
                        commit=git_ls_remote(dep.url, dep.ref),
                        target_path=dep.target_path,
                    )
                )
            else:
                raise ValueError(f"Unexpected external input type {type(dep)}")

        builder_deps = StableDescriptor._make_stable_files(
            [
                dep
                for dep in descriptor.inputs.builders
                if not isinstance(dep, EnvInput)
            ],
            absolute_path,
        )

        targets = []
        for target in descriptor.targets or []:
            if isinstance(target, ImageTarget):
                dockerfile = target.dockerfile
                if dockerfile is None:
                    dockerfile = PurePath("Dockerfile")
                dockerfile_path = absolute_path / dockerfile
                if not dockerfile_path.exists():
                    raise ValueError(f"Dockerfile {dockerfile_path} does not exist")

                platform = None
                if target.platform is not None and not isinstance(
                    target.platform, Platform
                ):
                    platform = Platform(target.platform)

                targets.append(
                    StableImageTarget(
                        repository=target.repository,
                        tag=target.tag,
                        dockerfile=PurePath(dockerfile),
                        dockerfile_absolute_path=dockerfile_path,
                        also_tag_with_content_id=target.also_tag_with_content_id,
                        platform=platform,
                    )
                )

                builder_deps.append(
                    StableFileInput(
                        path=PurePath(dockerfile),
                        absolute_path=dockerfile_path,
                    )
                )
            else:
                raise ValueError(f"Unexpected target type {type(target)}")

        inputs = StableInputs(
            files=file_deps,
            builders=builder_deps,
            envs=env_deps,
            external=external_deps,
        )

        return StableDescriptor(
            absolute_path=absolute_path,
            inputs=inputs,
            targets=targets,
        )


class DescriptorEncoder(json.JSONEncoder):
    def default(self, o):
        from pathlib import PurePosixPath

        if isinstance(o, PurePosixPath):
            o = str(o)
            return o

        return json.JSONEncoder.default(self, o)
