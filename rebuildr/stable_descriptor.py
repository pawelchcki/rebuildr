from dataclasses import asdict, dataclass, field
import glob
import hashlib
import json
import os
from pathlib import Path, PurePath
from typing import Optional, Self

from rebuildr.descriptor import (
    Descriptor,
    Dockerfile,
    EnvInput,
    FileInput,
    GlobInput,
    TagTarget,
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
class StableFileInput:
    path: PurePath
    absolute_path: Path

    def sort_key(self) -> str:
        return str(self.path)

    def read_to_string(self) -> str:
        with open(self.absolute_path, "r") as f:
            return f.read()

    def hash_update(self, hasher):
        hasher.update(self.read_to_string().encode())
        print(self.read_to_string())


@dataclass
class StableInputs:
    envs: list[StableEnvInput]
    files: list[FileInput] = field(default_factory=list)
    builders: list[FileInput] = field(default_factory=list)

    def sha_sum(self):
        m = hashlib.sha256()
        for env_dep in sorted(self.envs, key=lambda x: x.sort_key()):
            env_dep.hash_update(m)

        # sort and iterate - order must be predictable - always
        for builder_dep in sorted(self.builders, key=lambda x: x.sort_key()):
            builder_dep.hash_update(m)

        for file_dep in sorted(self.files, key=lambda x: x.sort_key()):
            file_dep.hash_update(m)

        return m.hexdigest()


@dataclass(frozen=True)
class StableDescriptor:
    absolute_path: Path
    inputs: StableInputs
    targets: Optional[list[TagTarget]] = None

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
    def _make_stable_files(files, absolute_path: Path) -> list[StableFileInput]:
        stable_files = []
        for file_dep in files:
            if isinstance(file_dep, FileInput):
                stable_files.append(
                    StableFileInput(
                        path=file_dep.path, absolute_path=absolute_path / file_dep.path
                    )
                )
            elif isinstance(file_dep, Dockerfile):
                stable_files.append(
                    StableFileInput(
                        path=file_dep.path, absolute_path=absolute_path / file_dep.path
                    )
                )
            elif isinstance(file_dep, GlobInput):
                glob_root = (
                    absolute_path
                    if file_dep.root_dir is None
                    else absolute_path / file_dep.root_dir
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
            else:
                raise ValueError(f"Unexpected input type {type(file_dep)}")
        return stable_files

    def from_descriptor(descriptor: Descriptor, absolute_path: Path) -> Self:
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
        builder_deps = StableDescriptor._make_stable_files(
            [
                dep
                for dep in descriptor.inputs.builders
                if not isinstance(dep, EnvInput)
            ],
            absolute_path,
        )
        inputs = StableInputs(files=file_deps, builders=builder_deps, envs=env_deps)

        return StableDescriptor(
            absolute_path=absolute_path,
            inputs=inputs,
            targets=descriptor.targets,
        )


class DescriptorEncoder(json.JSONEncoder):
    def default(self, obj):
        from pathlib import PurePosixPath

        if isinstance(obj, PurePosixPath):
            obj = str(obj)
            return obj

        return json.JSONEncoder.default(self, obj)
