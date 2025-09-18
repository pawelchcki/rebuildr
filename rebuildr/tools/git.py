from pathlib import Path
import logging
import subprocess
from typing import List


def git_command(args: List[str], **kwargs):
    if kwargs.get("check") is None:
        kwargs["check"] = True
    try:
        return subprocess.run(["git"] + args, **kwargs)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Git command failed: {' '.join(['git'] + args)} - {e}")
    except FileNotFoundError:
        raise RuntimeError("Git command not found. Please ensure git is installed and in PATH.")


def git_clone(url: str, target_path: Path, ref: str):
    logging.info(f"Cloning {url} to {target_path}")
    git_command(["clone", url, str(target_path)])

    git_checkout(target_path, ref)


def git_better_clone(url: str, target_path: Path, ref: str):
    if (target_path / ".git").exists():
        logging.info(f"Reusing {target_path}")
        git_checkout(target_path, ref, force=True)
    else:
        target_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Cloning {url} to {target_path}")
        git_command(["init", str(target_path)])
        git_command(["remote", "add", "origin", url], cwd=str(target_path))
        git_command(["fetch", "origin", ref], cwd=str(target_path))
        git_checkout(target_path, ref, force=True)


def git_checkout(repo_path: Path, ref: str, force: bool = False):
    logging.info(f"Checking out {ref} in {repo_path}")
    args = ["checkout"]
    if force:
        args.append("--force")
    args.append(ref)
    git_command(args, cwd=str(repo_path))


def git_ls_remote(url: str, ref: str) -> str:
    logging.info(f"Listing remote for {url} with ref {ref}")
    try:
        result = git_command(
            ["ls-remote", "--heads", "--tags", url, ref],
            capture_output=True,
            text=True,
        )
        if not result.stdout:
            raise ValueError(f"Ref {ref} not found in {url}")

        # The output is in the format <hash>\t<ref>, we are interested in the hash
        return result.stdout.split()[0]
    except Exception as e:
        raise RuntimeError(f"Failed to list remote refs for {url}: {e}")
