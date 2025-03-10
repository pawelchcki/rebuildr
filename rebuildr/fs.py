from pathlib import Path
import tempfile


class File(object):
    def __init__(self):
        self.contents = contents
        self.tmp_file = tempfile.NamedTemporaryFile()
        self.tmp_file.write(self.contents.encode())
        self.tmp_file.seek(0)

    def path_in_container(self):
        raise "todo"

    def copy_to_staged_ctx(self, ctx):
        raise "todo"


class Context(object):
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.files = []

    def add_file(self, file):
        self.files.append(file)

    def copy_to(self, dest):
        raise "todo"
