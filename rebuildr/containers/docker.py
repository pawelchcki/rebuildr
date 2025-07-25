import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional


def is_docker_available() -> bool:
    return shutil.which("docker") is not None


def docker_bin() -> Path:
    if not is_docker_available():
        raise ValueError("docker is not available")

    return Path(shutil.which("docker"))


def docker_image_exists_locally(image_tag: str) -> bool:
    command = [str(docker_bin()), "image", "inspect", image_tag]
    logging.info("Running docker command: {}".format(" ".join(command)))
    try:
        exit_code = subprocess.run(command, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError:
        return False


def docker_image_exists_in_registry(image_tag: str) -> bool:
    # Use docker manifest inspect to check if image exists in registry
    command = [str(docker_bin()), "manifest", "inspect", image_tag]
    logging.info("Running docker command: {}".format(" ".join(command)))
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=100)
        return True
    except subprocess.TimeoutExpired:
        logging.info(
            "Timeout waiting for docker manifest inspect - check VPN connection"
        )
        return False
    except subprocess.CalledProcessError:
        return False


def docker_pull_image(image_tag: str):
    command = [str(docker_bin()), "pull", image_tag]
    logging.info("Running docker command: {}".format(" ".join(command)))
    subprocess.run(command, check=True)


def docker_push_image(image_tag: str, overwrite_in_registry: bool):
    command = [str(docker_bin()), "push", image_tag]
    if not overwrite_in_registry:
        exists = docker_image_exists_in_registry(image_tag)
        if exists:
            logging.info(f"Image {image_tag} already exists in registry")
            return

    logging.info("Running docker command: {}".format(" ".join(command)))
    subprocess.run(command, check=True)
