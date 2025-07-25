load("@bazel_skylib//lib:shell.bzl", "shell")
load("//bzl/rule:providers.bzl", "RebuildrInfo")

def build_copy_commands(work_dir, input_attrs):
    """
    Builds a list of shell commands to copy files from targets to a work directory.

    This function creates commands that preserve the directory structure of source files
    while copying them to the work directory. It handles both source files and generated files.

    Args:
        work_dir: The directory where files should be copied to.
        input_attrs: The list of targets to copy files from.

    Returns:
        A list of shell commands to execute for copying files.
    """

    # Create a command to copy files to the work directory, preserving directory structure
    copy_commands = []

    # Track directories we've already created
    created_dirs = {}

    for target in input_attrs:
        # Process all files from this target
        for f in target.files.to_list():
            root = target.label.package

            # Get the path relative to the package
            if f.is_source:
                # Strip the root package path from the short_path if it's a prefix
                path = f.short_path
                if root != "" and path.startswith(root + "/"):
                    path = path[len(root) + 1:]  # +1 for the slash

                # For source files, we need to preserve their path within the package
                path_parts = path.split("/")
                if len(path_parts) > 1:
                    # Create parent directories if needed
                    dir_path = ""
                    for part in path_parts[:-1]:
                        dir_path = dir_path + "/" + part if dir_path else part
                        if dir_path not in created_dirs:
                            copy_commands.append("mkdir -p {}/{}".format(work_dir.path, dir_path))
                            created_dirs[dir_path] = True

                    # Copy the file to the appropriate subdirectory
                    copy_commands.append("cp {} {}/{}".format(
                        f.path,
                        work_dir.path,
                        "/".join(path_parts[:-1]),
                    ))
                else:
                    # Files at the root level
                    copy_commands.append("cp {} {}".format(f.path, work_dir.path))
            else:
                # For generated files, we just copy them to the root of the work directory
                copy_commands.append("cp {} {}".format(f.path, work_dir.path))

    return "\n".join(copy_commands)

def _rebuildr_impl(ctx):
    # Get the input files
    input_files = ctx.files.srcs
    input_attrs = ctx.attr.srcs

    descriptor_file = ctx.file.descriptor

    metadata_file = ctx.actions.declare_file(ctx.label.name + ".stable")
    stable_image_tag = ctx.actions.declare_file(ctx.label.name + ".stable_image_tag")

    work_dir = ctx.actions.declare_directory(ctx.label.name + ".work_dir")

    copy_commands = """
    set -eux
    mkdir -p {out_dir}

    {copy_commands}
    """.format(copy_commands = build_copy_commands(work_dir, input_attrs), out_dir = shell.quote(work_dir.path))

    copy_files_sh = ctx.actions.declare_file(ctx.label.name + ".copy_files.sh")
    ctx.actions.write(output = copy_files_sh, content = copy_commands, is_executable = True)

    ctx.actions.run_shell(
        inputs = input_files,
        outputs = [work_dir],
        command = copy_files_sh.path,
        tools = [copy_files_sh],
    )

    # We need to use the runfiles directory to make Python happy
    runfiles_dir = ctx.executable._rebuildr_tool.path + ".runfiles"

    build_args_arg = " ".join([shell.quote("{k}={v}".format(k = k, v = v)) for k, v in ctx.attr.build_args.items()])
    env_declarations = "\n".join(["export {k}={v}".format(k = shell.quote(k), v = shell.quote(v)) for k, v in ctx.attr.build_env.items()])

    # Build the command that will run rebuildr using the right Python environment
    command = """
    set -xe
    # Set up the Python environment to find runfiles
    # export PYTHONPATH="{runfiles_dir}"

    export REBUILDR_OVERRIDE_ROOT_DIR={work_dir}

    {env_declarations}

    # Run the rebuildr tool
    {rebuildr} load-py {descriptor} {build_args_arg} bazel-stable-metadata {metadata_file} {stable_image_tag}
    """.format(
        runfiles_dir = runfiles_dir,
        rebuildr = shell.quote(ctx.executable._rebuildr_tool.path),
        descriptor = shell.quote(descriptor_file.path),
        metadata_file = shell.quote(metadata_file.path),
        stable_image_tag = shell.quote(stable_image_tag.path),
        work_dir = shell.quote(work_dir.path),
        build_args_arg = build_args_arg,
        env_declarations = env_declarations,
    )

    # Execute the rebuildr tool with the right environment
    ctx.actions.run_shell(
        inputs = input_files + [work_dir],
        outputs = [metadata_file, stable_image_tag],
        command = command,
        env = ctx.attr.build_env,
        tools = [ctx.executable._rebuildr_tool, descriptor_file],
        progress_message = "Running rebuildr on %s" % ctx.label,
        use_default_shell_env = True,
    )

    # Create runfiles with the tool and descriptor file
    # This isn't working because we need to include the transitive runfiles of the _rebuildr_tool
    # The tool likely has Python dependencies that need to be included
    runfiles = ctx.runfiles(files = [ctx.executable._rebuildr_tool, descriptor_file, work_dir])

    # Merge with the default runfiles of the rebuildr tool to get all its dependencies
    runfiles = runfiles.merge(ctx.attr._rebuildr_tool[DefaultInfo].default_runfiles)

    executable_output = ctx.actions.declare_file(ctx.label.name + ".sh")
    ctx.actions.write(output = executable_output, is_executable = True, content = command)

    # Return both DefaultInfo and our custom provider
    return [
        DefaultInfo(
            files = depset([metadata_file, stable_image_tag]),
            executable = executable_output,
            runfiles = runfiles,
        ),
        RebuildrInfo(
            descriptor = descriptor_file,
            work_dir = work_dir,
            stable_file = metadata_file,
            stable_image_tag = stable_image_tag,
            build_env = ctx.attr.build_env,
            build_args = ctx.attr.build_args,
        ),
    ]

# Define the rule
rebuildr_image = rule(
    implementation = _rebuildr_impl,
    outputs = {
        "stable": "%{name}.stable",
    },
    executable = True,
    attrs = {
        "srcs": attr.label_list(
            allow_files = True,
            doc = "Source files to include in the build context",
        ),
        "descriptor": attr.label(
            allow_single_file = [".py"],
            mandatory = True,
            doc = "Python descriptor file for the rebuildr build",
        ),
        "build_env": attr.string_dict(
            doc = "Docker build nvironment variables to set for the image build",
            default = {},
        ),
        "build_args": attr.string_dict(
            doc = "Docker build arguments to pass to the image build",
            default = {},
        ),
        "_rebuildr_tool": attr.label(
            default = Label("//rebuildr:rebuildr"),
            executable = True,
            cfg = "exec",
            doc = "The rebuildr executable",
        ),
    },
    doc = "Builds a Docker image using the rebuildr tool",
)
