from pathlib import Path
import logging
import subprocess
from typing import List


def git_command(args: List[str], **kwargs):
    if kwargs.get("check") is None:
        kwargs["check"] = True
    return subprocess.run(["git"] + args, **kwargs)


def git_clone(url: str, target_path: Path, ref: str):
    logging.info(f"Cloning {url} to {target_path}")
    git_command(["clone", url, str(target_path)])

    logging.info(f"Checking out {ref}")
    git_command(["checkout", ref], cwd=str(target_path))


def git_checkout(repo_path: Path, ref: str):
    logging.info(f"Checking out {ref} in {repo_path}")
    git_command(["checkout", ref], cwd=str(repo_path))


def git_ls_remote(url: str, ref: str) -> str:
    logging.info(f"Listing remote for {url} with ref {ref}")
    result = git_command(
        ["ls-remote", "--heads", "--tags", url, ref],
        capture_output=True,
        text=True,
    )
    if not result.stdout:
        raise ValueError(f"Ref {ref} not found in {url}")

    # The output is in the format <hash>\t<ref>, we are interested in the hash
    return result.stdout.split()[0]
