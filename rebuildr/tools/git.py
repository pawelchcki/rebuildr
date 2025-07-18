from pathlib import Path
import logging


def git_clone(url: str, target_path: Path, commit: str):
    import subprocess

    logging.info(f"Cloning {url} to {target_path}")
    subprocess.run(["git", "clone", url, str(target_path)], check=True)

    logging.info(f"Checking out {commit}")
    subprocess.run(["git", "checkout", commit], cwd=str(target_path), check=True)
