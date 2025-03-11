import inspect
import os
from pathlib import Path, PurePath
import shutil
import tempfile


class VirtualFile(object):
    def __init__(self, contents):
        self.contents = contents
        self.tmp_file = tempfile.NamedTemporaryFile()
        self.tmp_file.write(self.contents.encode())
        self.tmp_file.seek(0)

    def path(self):
        return Path(self.tmp_file.name)


class Dockerfile(object):
    dockerfile = Path
    root_dir = Path

    def __init__(
        self,
        root_dir,
        dockerfile: Path | None = None,
        dockerfile_contents: str | None = None,
    ):
        self.dockerfile = dockerfile
        self.virtual_files = []

        if dockerfile_contents and not dockerfile:
            dockerfile = VirtualFile(dockerfile_contents)
            self.virtual_files.append(dockerfile)
            self.dockerfile = dockerfile.path()

        self.root_dir = root_dir
        self.fs_dependencies = {}
        self.isolated_build = False

    def isolated_paths_mapped(self, mapped_paths):
        self.isolated_build = True
        root_dir = self.root_dir
        if not root_dir.is_absolute():
            parent = Path(inspect.stack()[1].filename).parent
            root_dir = parent / root_dir

        for target, src in mapped_paths.items():
            if isinstance(src, VirtualFile):
                self.virtual_files.append(src)
                src = src.path()
            src_path = Path(src)
            if not src_path.is_absolute():
                src_path = root_dir / src_path
            self.fs_dependencies[target] = src_path

        return self

    def isolated_paths(self, *paths):
        self.isolated_build = True
        root_dir = self.root_dir
        if not root_dir.is_absolute():
            parent = Path(inspect.stack()[1].filename).parent
            root_dir = parent / root_dir

        for path in paths:
            path = Path(path)
            self.fs_dependencies[path] = root_dir / path

        return self

    def _isolated_build(self, workdir_path, args):
        context_path = workdir_path / "context"
        os.makedirs(context_path)

        files_to_copy = {}
        for target, src in self.fs_dependencies.items():
            target = PurePath(target)
            if target.is_absolute():
                target = target.relative_to("/")
            files_to_copy[context_path / target] = src

        for target, _ in files_to_copy.items():
            path = target.parent
            os.makedirs(path, exist_ok=True)

        for target, src in files_to_copy.items():
            if src.is_file():
                shutil.copyfile(src, target, follow_symlinks=True)
                shutil.copymode(src, target, follow_symlinks=True)
            else:
                shutil.copytree(src, target)

        builder = _CLIBuilder(None)
        res = builder.build(context_path, dockerfile=self.dockerfile, buildargs=args)

        return res

    def build(self, args=None):
        if self.isolated_build:
            temp_dir = tempfile.TemporaryDirectory()
            return self._isolated_build(Path(temp_dir.name), args)
        else:
            builder = _CLIBuilder(None)
            return builder.build(
                self.root_dir, dockerfile=self.dockerfile, buildargs=args
            )

    def image(self):
        return Image(self.build())

    def __str__(self):
        return f"Image. Dockerfile: {self.dockerfile}"
