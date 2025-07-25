from dataclasses import asdict, dataclass, field
import glob
import hashlib
import json
import os
from pathlib import Path, PurePath
from typing import Optional, Self

from rebuildr.descriptor import (
    ArgsInput,
    Descriptor,
    EnvInput,
    FileInput,
    GlobInput,
    ImageTarget,
    GitHubCommitInput,
    Platform,
)


# class holds copy of os env and passed build args
class StableEnvironment:
    env: dict[str, str]
    build_args: dict[str, str]

    def __init__(self, env: dict[str, str], build_args: dict[str, str]):
        self.env = env
        self.build_args = build_args

    def get_env(self, key: str) -> str:
        return self.env.get(key)

    def get_build_arg(self, key: str) -> str:
        return self.build_args.get(key)

    @staticmethod
    def from_os_env(build_args: Optional[dict[str, str]] = None) -> "StableEnvironment":
        return StableEnvironment(os.environ, build_args or {})


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

    def hash_update(self, hasher, env: StableEnvironment):
        value = env.get_env(self.key)

        if value is None and self.default is not None:
            value = self.default

        if value or value == "":
            hasher.update(self.key.encode())
        if value:
            hasher.update(value.encode())


@dataclass
class StableBuildArgsInput(BaseInput):
    key: str
    default: Optional[str] = None

    def sort_key(self) -> str:
        return self.key

    def hash_update(self, hasher, env: StableEnvironment):
        value = env.get_build_arg(self.key)
        if value is None:
            value = self.default
        if value:
            hasher.update(self.key.encode())
            hasher.update(value.encode())


@dataclass
class StableGitHubCommitInput(BaseInput):
    url: str
    commit: str
    target_path: str | PurePath

    def sort_key(self) -> str:
        return f"{self.url}/{self.commit}"

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
    build_args: list[StableBuildArgsInput]
    files: list[StableFileInput] = field(default_factory=list)
    builders: list[StableFileInput] = field(default_factory=list)
    external: list[StableGitHubCommitInput] = field(default_factory=list)

    def sha_sum(self, env: StableEnvironment):
        m = hashlib.sha256()
        for env_dep in sorted(self.envs, key=lambda x: x.sort_key()):
            env_dep.hash_update(m, env)

        for build_arg_dep in sorted(self.build_args, key=lambda x: x.sort_key()):
            build_arg_dep.hash_update(m, env)

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

    def image_tags(self, inputs: StableInputs, env: StableEnvironment) -> list[str]:
        tags = []
        if self.tag:
            tags.append(self.repository + ":" + self.tag)
        if self.also_tag_with_content_id:
            tags.append(self.content_id_tag(inputs, env))

        return tags

    def content_id_tag(self, inputs: StableInputs, env: StableEnvironment) -> str:
        if self.platform is None:
            return f"{self.repository}:src-id-{inputs.sha_sum(env)}"
        else:
            platform_prefix = self.platform.value.replace("/", "-")
            return f"{self.repository}:{platform_prefix}-src-id-{inputs.sha_sum(env)}"


@dataclass(frozen=True)
class StableDescriptor:
    absolute_path: Path
    inputs: StableInputs
    targets: Optional[list[StableImageTarget]] = None

    def sha_sum(self, env: StableEnvironment):
        return self.inputs.sha_sum(env)

    def stable_inputs_dict(self, env: StableEnvironment):
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

        inputs = clean_dict(asdict(self.inputs))
        envs = inputs["envs"]
        for in_env in envs:
            value = env.get_env(in_env["key"])
            if value:
                in_env["value"] = value

        build_args = inputs["build_args"]
        for in_build_arg in build_args:
            value = env.get_build_arg(in_build_arg["key"])
            if value:
                in_build_arg["value"] = value

        return {
            "inputs": inputs,
            "sha256": self.sha_sum(env),
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
        build_args_deps = [
            StableBuildArgsInput(key=dep.key, default=dep.default)
            for dep in descriptor.inputs.builders
            if isinstance(dep, ArgsInput)
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
            else:
                raise ValueError(f"Unexpected external input type {type(dep)}")

        builder_deps = StableDescriptor._make_stable_files(
            [
                dep
                for dep in descriptor.inputs.builders
                if not isinstance(dep, EnvInput) and not isinstance(dep, ArgsInput)
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
            build_args=build_args_deps,
            external=external_deps,
        )

        return StableDescriptor(
            absolute_path=absolute_path,
            inputs=inputs,
            targets=targets,
        )

    def filter_env_and_build_args(self, env: StableEnvironment) -> StableEnvironment:
        return StableEnvironment(
            env={
                k: v
                for k, v in env.env.items()
                if k in [env_dep.key for env_dep in self.inputs.envs]
            },
            build_args={
                k: v
                for k, v in env.build_args.items()
                if k in [build_arg_dep.key for build_arg_dep in self.inputs.build_args]
            },
        )


class DescriptorEncoder(json.JSONEncoder):
    def default(self, obj):
        from pathlib import PurePosixPath

        if isinstance(obj, PurePosixPath):
            obj = str(obj)
            return obj

        return json.JSONEncoder.default(self, obj)
