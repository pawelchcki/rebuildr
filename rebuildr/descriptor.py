import hashlib
import os
from typing import Optional

from dataclasses import dataclass


@dataclass(frozen=True)
class EnvInput:
    key: str
    default: Optional[str] = None


# this dataclass should serialize to single string
@dataclass(frozen=True)
class FileInput:
    path: str

    def read_to_string(self):
        with open(self.path, "r") as f:
            return f.read()


@dataclass(frozen=True)
class Dockerfile:
    path: str

    def read_to_string(self):
        with open(self.path, "r") as f:
            return f.read()




@dataclass
class StrictInputs:
    env: list[EnvInput]
    files: list[FileInput]
    dockerfile: Optional[Dockerfile]

    def sha_sum(self, root_path):
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

@dataclass(frozen=True)
class Inputs:
    env: Optional[list[EnvInput|str]]
    files: Optional[list[FileInput|str]]
    dockerfile: Optional[Dockerfile|str]

    def into_strict(self, root_path):
        return StrictInputs(
            env=[EnvInput(key=x) if isinstance(x, str) else EnvInput(x) for x in self.env],
            files=[FileInput(x) if isinstance(x, str) else x for x in self.files],
            dockerfile=Dockerfile(self.dockerfile) if isinstance(self.dockerfile, str) else self.dockerfile,
        )
        
@dataclass
class Descriptor:
    inputs: Inputs

    def sha_sum(self, root_path):
        return self.inputs.sha_sum(root_path)
