import glob
import hashlib
import json
import os
from pathlib import PurePath
from typing import Optional

from dataclasses import asdict, dataclass, field


@dataclass
class EnvInput:
    key: str
    default: Optional[str] = None


# this dataclass should serialize to single string
@dataclass
class FileInput:
    path: str
    _relative_path: Optional[PurePath] = field(default=None, init=False, repr=False)

    def read_to_string(self):
        with open(self.path, "r") as f:
            return f.read()


@dataclass
class GlobInput:
    pattern: str
    root_dir: Optional[PurePath] = None

    def read_to_string(self):
        with open(self.path, "r") as f:
            return f.read()


@dataclass
class Dockerfile:
    path: str

    def read_to_string(self):
        with open(self.path, "r") as f:
            return f.read()


@dataclass
class Inputs:
    env: Optional[list[EnvInput]]
    files: Optional[list[FileInput]]
    dockerfile: Optional[Dockerfile | str]

    def sha_sum(self):
        m = hashlib.sha256()
        # sort and iterate - order must be predictable - always
        for env in sorted(self.env, key=lambda x: x.key):
            m.update(env.key.encode())
            if env.default:
                m.update(env.default.encode())
            else:
                # read from environment
                v = os.environ.get(env.key)
                if v:
                    m.update(v.encode())
        for file in sorted(self.files, key=lambda x: x.path):
            m.update(file.read_to_string().encode())

        if self.dockerfile:
            dockerfile = None
            if isinstance(self.dockerfile, Dockerfile):
                dockerfile = self.dockerfile
            else:
                dockerfile = Dockerfile(self.dockerfile)
            m.update(dockerfile.read_to_string().encode())
        return m.hexdigest()


@dataclass
class TagTarget:
    repository: str
    tag: Optional[str] = None


@dataclass
class Descriptor:
    inputs: Inputs
    targets: Optional[list[TagTarget]] = None

    def sha_sum(self):
        return self.inputs.sha_sum()

    def as_dict(self):
        return {
            "image": asdict(self),
            "sha256": self.sha_sum(),
        }

    def postprocess_paths(self, root_path: PurePath):
        file_inputs = [f for f in self.inputs.files if isinstance(f, FileInput)]
        other_file_inputs = [
            f for f in self.inputs.files if not isinstance(f, FileInput)
        ]
        self.inputs.files = file_inputs

        for file in self.inputs.files:
            file._relative_path = PurePath(file.path)
            file.path = os.path.join(root_path, file.path)

        for file in other_file_inputs:
            if isinstance(file, GlobInput):
                if file.root_dir:
                    file.root_dir = root_path / file.root_dir
                else:
                    file.root_dir = root_path

                for e in glob.glob(
                    file.pattern, root_dir=file.root_dir, recursive=True
                ):
                    fi = FileInput(file.root_dir / e)
                    fi._relative_path = PurePath(e)
                    self.inputs.files.append(fi)

        if isinstance(self.inputs.dockerfile, Dockerfile):
            self.inputs.dockerfile.path = root_path / self.inputs.dockerfile.path
        else:
            self.inputs.dockerfile = Dockerfile(root_path / self.inputs.dockerfile)
        return self


class DescriptorEncoder(json.JSONEncoder):
    def default(self, obj):
        from pathlib import PurePosixPath

        if isinstance(obj, PurePosixPath):
            obj = str(obj)
            return obj

        return json.JSONEncoder.default(self, obj)
