import logging
from pathlib import Path
from typing import Optional

from rebuildr.containers.docker import (
    docker_image_exists_in_registry,
    docker_image_exists_locally,
    docker_pull_image,
    docker_push_image,
    is_docker_available,
)


def image_exists_locally(image_tag: str) -> bool:
    if is_docker_available():
        return docker_image_exists_locally(image_tag)

    logging.warning("Docker is not available to check image existence")
    return False


def image_exists_in_registry(image_tag: str) -> bool:
    if is_docker_available():
        return docker_image_exists_in_registry(image_tag)

    logging.warning("Docker is not available to check image existence")
    return False


def pull_image(image_tag: str):
    if is_docker_available():
        docker_pull_image(image_tag)
    else:
        logging.warning("Docker is not available to pull image")


def push_image(image_tag: str, overwrite_in_registry: bool = False):
    if is_docker_available():
        docker_push_image(image_tag, overwrite_in_registry)
    else:
        logging.warning("Docker is not available to push image")
