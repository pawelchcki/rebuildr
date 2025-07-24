load("@bazel_skylib//lib:shell.bzl", "shell")
load("//bzl/rule:providers.bzl", "RebuildrInfo")

def _rebuildr_derive_impl(ctx):
    # Get the RebuildrInfo provider from the src
    rebuildr_info = ctx.attr.src[RebuildrInfo]

    metadata_file = ctx.actions.declare_file(ctx.label.name + ".stable")
    stable_image_tag = ctx.actions.declare_file(ctx.label.name + ".stable_image_tag")

    work_dir = rebuildr_info.work_dir
    build_args = dict(rebuildr_info.build_args)
    build_args.update(ctx.attr.build_args)
    build_env = dict(rebuildr_info.build_env)
    build_env.update(ctx.attr.build_env)
    descriptor_file = rebuildr_info.descriptor

    # We need to use the runfiles directory to make Python happy
    runfiles_dir = ctx.executable._rebuildr_tool.path + ".runfiles"

    build_args_arg = " ".join([shell.quote("{k}={v}".format(k = k, v = v)) for k, v in build_args.items()])
    env_declarations = "\n".join(["export {k}={v}".format(k = shell.quote(k), v = shell.quote(v)) for k, v in build_env.items()])

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
        inputs = [work_dir],
        outputs = [metadata_file, stable_image_tag],
        command = command,
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
            build_env = build_env,
            build_args = build_args,
        ),
    ]

# Define the rule
rebuildr_derive = rule(
    implementation = _rebuildr_derive_impl,
    outputs = {
        "stable": "%{name}.stable",
    },
    executable = True,
    attrs = {
        "src": attr.label(
            doc = "The rebuildr_image target to derive from",
            providers = [RebuildrInfo],
            mandatory = True,
        ),
        "build_env": attr.string_dict(
            doc = "Docker build nvironment variables to set for the derived image build",
            default = {},
        ),
        "build_args": attr.string_dict(
            doc = "Docker build arguments to pass to the derived image build",
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
