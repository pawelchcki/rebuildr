from pathlib import PurePath


def target_path_is_set(target_path: str | PurePath, klass: type):
    if not target_path or target_path == "":
        raise ValueError(f"{klass.__name__}.target_path must be set and not empty")


def target_path_is_not_root(target_path: str | PurePath, klass: type):
    path = PurePath(target_path)

    if path == "." or path == "/":
        raise ValueError(
            f"{klass.__name__}.target_path={target_path} must not be the root directory"
        )
