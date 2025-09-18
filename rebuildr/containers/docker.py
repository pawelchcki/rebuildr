import logging
import shutil
import socket
import subprocess
from pathlib import Path
import urllib


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
        subprocess.run(command, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError:
        return False


def docker_image_exists_in_registry(image_tag: str) -> bool:
    # check if external registry can be dns resolved before fetching manifest

    hostname = image_tag.split("/")[0]
    # hostname must have at least one dot to attempt to resolve
    if "." in hostname:
        logging.info(f"Attempting to resolve hostname {hostname}")
        try:
            socket.gethostbyname(hostname)
        except socket.gaierror:
            logging.info(f"Could not resolve hostname {hostname}")
            return False

        # send a http request using built in python library to the hostname with a 5 second timeout
        try:
            urllib.request.urlopen(f"http://{hostname}", timeout=1)
        except Exception:
            logging.info(f"Could not resolve hostname {hostname} via http")
            return False
    else:
        logging.debug(
            f"Hostname {hostname} does not have a dot, skipping DNS resolution"
        )

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
