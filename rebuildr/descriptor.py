from enum import Enum
from pathlib import PurePath
from typing import Optional

from dataclasses import dataclass, field


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


@dataclass
class Inputs:
    files: list[str | FileInput | GlobInput] = field(default_factory=list)
    builders: list[str | EnvInput | FileInput | ArgsInput | GlobInput] = field(
        default_factory=list
    )
    external: list[str | GitHubCommitInput] = field(default_factory=list)


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
