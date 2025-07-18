"""
Rule for building container images using rebuildr.

This rule processes a descriptor file and source files to build container images.
It handles file copying while preserving directory structure, and executes the
rebuildr tool to build the specified images.

Args:
    name: A unique name for this rule.
    srcs: Source files to include in the build context.
    descriptor: A Python file containing a rebuildr.Descriptor object.
"""

load("//bzl/rule:image.bzl", _rebuildr_image = "rebuildr_image")
load("//bzl/rule:materialize.bzl", _rebuildr_materialize = "rebuildr_materialize")
load("//bzl/rule:push.bzl", _rebuildr_push = "rebuildr_push")

rebuildr_materialize = _rebuildr_materialize
rebuildr_image = _rebuildr_image
rebuildr_push = _rebuildr_push
