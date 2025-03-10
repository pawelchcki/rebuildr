import hashlib
import os
from pathlib import PurePath
from typing import Optional

from dataclasses import dataclass


@dataclass
class EnvInput:
    key: str
    default: Optional[str] = None


# this dataclass should serialize to single string
@dataclass
class FileInput:
    path: str
    _relative_path: Optional[PurePath] = None

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
class Descriptor:
    inputs: Inputs

    def sha_sum(self):
        return self.inputs.sha_sum()

    def postprocess_paths(self, root_path):
        for file in self.inputs.files:
            file._relative_path = PurePath(file.path)
            file.path = os.path.join(root_path, file.path)

        if isinstance(self.inputs.dockerfile, Dockerfile):
            self.inputs.dockerfile.path = os.path.join(
                root_path, self.inputs.dockerfile.path
            )
        else:
            self.inputs.dockerfile = Dockerfile(
                os.path.join(root_path, self.inputs.dockerfile)
            )
        return self
