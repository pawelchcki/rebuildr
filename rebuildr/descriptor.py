from enum import Enum
import glob
import hashlib
import json
import os
from pathlib import Path, PurePath
from typing import Optional, Self

from dataclasses import asdict, dataclass, field
from rebuildr import validators


@dataclass
class FileInput:
    path: str | PurePath


@dataclass
class GlobInput:
    pattern: str
    root_dir: Optional[str | PurePath] = None


@dataclass
class EnvInput:
    key: str
    default: Optional[str] = None


@dataclass
class ArgsInput:
    key: str
    default: Optional[str] = None


@dataclass
class GitHubCommitInput:
    owner: str
    repo: str
    commit: str
    target_path: str | PurePath

    def __post_init__(self):
        validators.target_path_is_set(self.target_path, self.__class__)
        validators.target_path_is_not_root(self.target_path, self.__class__)


@dataclass
class GitRepoInput:
    url: str
    ref: str
    target_path: str | PurePath

    def __post_init__(self):
        validators.target_path_is_set(self.target_path, self.__class__)
        validators.target_path_is_not_root(self.target_path, self.__class__)


@dataclass
class Inputs:
    files: list[str | FileInput | GlobInput] = field(default_factory=list)
    builders: list[str | EnvInput | FileInput | ArgsInput | GlobInput] = field(
        default_factory=list
    )
    external: list[str | GitHubCommitInput | GitRepoInput] = field(default_factory=list)


@dataclass
class Platform(Enum):
    LINUX_AMD64 = "linux/amd64"
    LINUX_ARM64 = "linux/arm64"


@dataclass
class ImageTarget:
    repository: str
    tag: Optional[str] = None
    also_tag_with_content_id: bool = True
    dockerfile: Optional[str | PurePath] = None
    platform: Optional[str | Platform] = None
    target: Optional[str] = None  # TODO: Targets are not supported yet


@dataclass
class Descriptor:
    inputs: Inputs
    targets: Optional[list[ImageTarget]] = None
