import glob
import hashlib
import json
import os
from pathlib import Path, PurePath
from typing import Optional, Self

from dataclasses import asdict, dataclass, field


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
class Inputs:
    files: list[str | FileInput | GlobInput] = field(default_factory=list)
    builders: list[str | EnvInput | FileInput | GlobInput] = field(default_factory=list)


@dataclass
class ImageTarget:
    repository: str
    tag: Optional[str] = None
    also_tag_with_content_id: bool = True
    dockerfile: Optional[str | PurePath] = None
    target: Optional[str] = None  # TODO: Targets are not supported yet


@dataclass
class Descriptor:
    inputs: Inputs
    targets: Optional[list[ImageTarget]] = None
