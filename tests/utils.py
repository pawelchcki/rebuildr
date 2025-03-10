
import os
from pathlib import Path

def resolve_current_dir(path: str) -> str:
    return Path(os.path.dirname(os.path.abspath(path)))