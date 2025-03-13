import glob
import hashlib
import json
import os
from pathlib import Path, PurePath
from typing import Optional, Self

from dataclasses import asdict, dataclass, field

@dataclass
class FileInput:
    path: str|PurePath

@dataclass
class GlobInput:    
    pattern: str
    root_dir: Optional[str|PurePath] = None

@dataclass
class EnvInput:
    key: str
    default: Optional[str] = None

@dataclass
class Dockerfile:
    path: str|PurePath

@dataclass
class Inputs:
    files: list[str | FileInput | Dockerfile | GlobInput] = field(default_factory=list)
    builders: list[str | EnvInput | FileInput | Dockerfile | GlobInput] = field(default_factory=list)

@dataclass
class TagTarget:
    repository: str
    tag: Optional[str] = None

@dataclass
class Descriptor:
    inputs: Inputs
    targets: Optional[list[TagTarget]] = None
