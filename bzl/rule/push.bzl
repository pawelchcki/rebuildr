load("@bazel_skylib//lib:shell.bzl", "shell")
load("//bzl/rule:derive.bzl", "build_args_string", "env_declarations_string")
load("//bzl/rule:providers.bzl", "RebuildrInfo")

# Bash helper function for looking up runfiles.
# Vendored from
# https://github.com/bazelbuild/bazel/blob/master/tools/bash/runfiles/runfiles.bash
BASH_RLOCATION_FUNCTION = """
# --- begin runfiles.bash initialization v3 ---
# Copy-pasted from the Bazel Bash runfiles library v3.
set -uo pipefail; set +e; f=bazel_tools/tools/bash/runfiles/runfiles.bash
source "${RUNFILES_DIR:-/dev/null}/$f" 2>/dev/null || \
  source "$(grep -sm1 "^$f " "${RUNFILES_MANIFEST_FILE:-/dev/null}" | cut -f2- -d' ')" 2>/dev/null || \
  source "$0.runfiles/$f" 2>/dev/null || \
  source "$(grep -sm1 "^$f " "$0.runfiles_manifest" | cut -f2- -d' ')" 2>/dev/null || \
  source "$(grep -sm1 "^$f " "$0.exe.runfiles_manifest" | cut -f2- -d' ')" 2>/dev/null || \
  { echo>&2 "ERROR: cannot find $f"; exit 1; }; f=; set -e
# --- end runfiles.bash initialization v3 ---
"""

def _rebuildr_push_impl(ctx):
    """Implementation of the rebuildr_push rule."""
    rebuildr_info = ctx.attr.src[RebuildrInfo]
    output = ctx.actions.declare_file(ctx.label.name + ".pushed")

    build_args = dict(rebuildr_info.build_args)
    build_env = dict(rebuildr_info.build_env)

    build_args_arg = build_args_string(build_args)
    env_declarations = env_declarations_string(build_env)

    command = BASH_RLOCATION_FUNCTION + """
    set -xe
    export REBUILDR_OVERRIDE_ROOT_DIR={work_dir}
    export BUILDX_CONFIG=$(mktemp -d)
    trap "rm -rf $BUILDX_CONFIG" EXIT
    set -xe

    {env_declarations}

    # Run the rebuildr tool to push the image
    find $REBUILDR_OVERRIDE_ROOT_DIR/
    {rebuildr} load-py {descriptor} {build_args_arg} push-image 
    """.format(
        rebuildr = shell.quote(ctx.executable._rebuildr_tool.short_path),
        build_args_arg = build_args_arg,
        env_declarations = env_declarations,
        descriptor = shell.quote(rebuildr_info.descriptor.short_path),
        work_dir = shell.quote(rebuildr_info.work_dir.short_path),
        output = shell.quote(output.path),
    )
    ctx.actions.write(output = output, content = command, is_executable = True)

    runfiles = ctx.runfiles(files = [ctx.file._bash_runfile_helper, ctx.executable._rebuildr_tool, rebuildr_info.descriptor, rebuildr_info.work_dir])
    runfiles = runfiles.merge(ctx.attr._rebuildr_tool[DefaultInfo].default_runfiles)

    return [
        DefaultInfo(
            files = depset([output]),
            executable = output,
            runfiles = runfiles,
        ),
    ]

rebuildr_push = rule(
    implementation = _rebuildr_push_impl,
    executable = True,
    attrs = {
        "src": attr.label(
            doc = "The rebuildr_image target to push",
            providers = [RebuildrInfo],
            mandatory = True,
        ),
        "_rebuildr_tool": attr.label(
            default = Label("//rebuildr:rebuildr"),
            executable = True,
            cfg = "exec",
            doc = "The rebuildr executable",
        ),
        "_bash_runfile_helper": attr.label(
            default = "@bazel_tools//tools/bash/runfiles",
            doc = "Label pointing to bash runfile helper",
            allow_single_file = True,
        ),
    },
    doc = "Pushes a Docker image built by rebuildr_image to a registry",
)
