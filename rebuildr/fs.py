from pathlib import Path, PurePath
import shutil
import tempfile

from rebuildr.descriptor import Descriptor, FileInput

class Context(object):
    def __init__(self, root_dir):
        self.root_dir = PurePath(root_dir)

    def copy_to(self, src: PurePath, dest: PurePath):
        # copy using python builtin src to root dir dest subpath
        dest_path = self.root_dir / dest
        dest_dir = dest_path.parent
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        shutil.copy(src, dest_path)

    def prepare_from_descriptor(self, descriptor: Descriptor):
        for file in descriptor.inputs.files:
            dest_path = self.root_dir / file.relative_path


            self.copy_to(file.path, file.relative_path)

    def from_descriptor(self, descriptor: Descriptor):
        for file in descriptor.inputs.files:
            self.add_file(RegularFile(file.path, file.relative_path))



        

        


