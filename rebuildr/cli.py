from dataclasses import asdict
import json
import os
from rebuildr.descriptor import Descriptor
import typer
# typer is used to speed up development - ideally for ease of embedding
# we shouldn't rely on 3rd party code a lot

import importlib.util
import sys

app = typer.Typer()


@app.command()
def hello(name: str):
    print(f"Hello {name}")


@app.command()
def parse_py(path: str) -> Descriptor:
    spec = importlib.util.spec_from_file_location("rebuildr.external.desc", path)
    foo = importlib.util.module_from_spec(spec)
    sys.modules["rebuildr.external.desc"] = foo
    spec.loader.exec_module(foo)
    absolute_dirname = os.path.dirname(os.path.abspath(path))
    image = foo.image.postprocess_paths(absolute_dirname)

    data = {
        "image": asdict(foo.image),
        "sha256": image.sha_sum(),
    }

    print(json.dumps(data, indent=4, sort_keys=True))

    return foo.image
