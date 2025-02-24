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


def import_in_path_dockerfiles():
    caller_frame = inspect.stack()[1]
    caller_module = inspect.getmodule(caller_frame[0])

    path = Path(caller_module.__file__).parent
    files = list(
        filter(lambda path: path.lower().endswith(".dockerfile"), os.listdir(path))
    )

    for file in files:
        attr_name = file[: file.rfind(".")]
        dockerfile = Dockerfile(path / file)
        setattr(caller_module, attr_name, dockerfile)


def dockerfile(dockerfile, *args, **kwargs):
    dockerfile = Path(dockerfile)
    if not dockerfile.is_absolute():
        parent = Path(inspect.stack()[1].filename).parent
        dockerfile = parent / dockerfile

    return Dockerfile(dockerfile=dockerfile, *args, **kwargs)


class _CLIBuilder(object):
    def __init__(self, progress):
        self._progress = progress
        # TODO: this setting should not rely on global env
        self.quiet = False if os.getenv("DOCKER_QUIET") is None else True

    def build(
        self,
        path,
        tag=None,
        nocache=False,
        pull=False,
        forcerm=False,
        dockerfile=None,
        container_limits=None,
        buildargs=None,
        cache_from=None,
        target=None,
    ):
        if dockerfile:
            dockerfile = os.path.join(path, dockerfile)
        iidfile = tempfile.mktemp()

        command_builder = _CommandBuilder()
        command_builder.add_params("--build-arg", buildargs)
        command_builder.add_list("--cache-from", cache_from)
        command_builder.add_arg("--file", dockerfile)
        command_builder.add_flag("--force-rm", forcerm)
        command_builder.add_flag("--no-cache", nocache)
        command_builder.add_flag("--progress", self._progress)
        command_builder.add_flag("--pull", pull)
        command_builder.add_arg("--tag", tag)
        command_builder.add_arg("--target", target)
        command_builder.add_arg("--iidfile", iidfile)
        args = command_builder.build([path])
        if self.quiet:
            with subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            ) as p:
                stdout, stderr = p.communicate()
                if p.wait() != 0:
                    # TODO: add better error handling
                    print(f"error building image: {dockerfile}")
                    print("------- STDOUT ---------")
                    print(stdout, end="")
                    print("----------------")
                    print()
                    print("------- STDERR ---------")
                    print(stderr, end="")
                    print("----------------")
        else:
            with subprocess.Popen(
                args, stdout=sys.stderr.buffer, universal_newlines=True
            ) as p:
                if p.wait() != 0:
                    print("TODO: error building image")

        with open(iidfile) as f:
            line = f.readline()
            image_id = line.split(":")[1].strip()
        os.remove(iidfile)
        return image_id


class _CommandBuilder(object):
    def __init__(self):
        self._args = ["docker", "build"]

    def add_arg(self, name, value):
        if value:
            self._args.extend([name, str(value)])

    def add_flag(self, name, flag):
        if flag:
            self._args.extend([name])

    def add_params(self, name, params):
        if params:
            for key, val in params.items():
                self._args.extend([name, "{}={}".format(key, val)])

    def add_list(self, name, values):
        if values:
            for val in values:
                self._args.extend([name, val])

    def build(self, args):
        return self._args + args
