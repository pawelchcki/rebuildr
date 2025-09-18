from pathlib import Path
import shutil
import tarfile
import tempfile

from rebuildr.stable_descriptor import (
    StableDescriptor,
)


class TarContext(object):
    def __init__(self):
        self.temp_file = tempfile.NamedTemporaryFile()
        self.temp_file_path = Path(self.temp_file.name)
        self.tar = tarfile.open(self.temp_file_path, "w:")

    def _add_file(self, src_path: Path, arcname: Path):
        """Add a single file to the tar archive ensuring parent directories exist.

        The tarfile module does not automatically include parent directories if
        they are not explicitly added. This helper makes sure the final archive
        structure matches the one created by LocalContext/prepare_from_descriptor.
        """

        # Ensure arcname is always presented as a posix path inside the archive
        arcname = Path(str(arcname)).as_posix()
        self.tar.add(src_path, arcname=arcname)

    def prepare_from_descriptor(self, descriptor: StableDescriptor):
        """Populate the internal tar file using the descriptor inputs.

        Only StableFileInput instances have an `absolute_src_path` attribute.
        Builders can contain other dependency types (eg. StableEnvInput) which
        should be ignored for tar creation purposes. We therefore silently skip
        objects without the expected attributes.
        """

        # Regular file inputs
        for file in descriptor.inputs.files:
            if hasattr(file, "absolute_src_path") and hasattr(file, "target_path"):
                self._add_file(file.absolute_src_path, file.target_path)

        # Builder file inputs (e.g. Dockerfiles) should also be included so that
        # the resulting context can be fed directly to `docker build`.
        for builder in descriptor.inputs.builders:
            # StableFileInput is the only builder variant that carries file data
            if hasattr(builder, "absolute_src_path") and hasattr(builder, "target_path"):
                self._add_file(builder.absolute_src_path, builder.target_path)

    def copy_to_file(self, path: Path):
        self.tar.close()
        shutil.copyfile(self.temp_file_path, path)
        # reopen file
        self.tar = tarfile.open(self.temp_file_path, "a:")
