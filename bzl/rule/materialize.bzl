load("@bazel_skylib//lib:shell.bzl", "shell")
load("//bzl/rule:providers.bzl", "RebuildrInfo")

def _rebuildr_materialize_impl(ctx):
    # Get the RebuildrInfo provider from the src
    rebuildr_info = ctx.attr.src[RebuildrInfo]
    
    # Create the executable output
    output = ctx.actions.declare_file(ctx.label.name + ".out")
    
    command = """
    set -eux
    
    export REBUILDR_OVERRIDE_ROOT_DIR={work_dir}
    export BUILDX_CONFIG=$(mktemp -d)
    trap "rm -rf $BUILDX_CONFIG" EXIT

    # Run the rebuildr tool to materialize the image
    {rebuildr} load-py {descriptor} materialize-image | tee {output}
    """.format(
        rebuildr = shell.quote(ctx.executable._rebuildr_tool.path),
        descriptor = shell.quote(rebuildr_info.descriptor.path),
        work_dir = shell.quote(rebuildr_info.work_dir.path),
        output = shell.quote(output.path),
    )
    
    ctx.actions.run_shell(
        inputs = [rebuildr_info.work_dir],
        outputs = [output],
        command = command,
        tools = [ctx.executable._rebuildr_tool, rebuildr_info.descriptor],
        execution_requirements = {"no-cache": "", "external": "", "no-remote": ""},
        use_default_shell_env = True,
    )
        
    return [DefaultInfo(
        files = depset([output]),
    )]

rebuildr_materialize = rule(
    implementation = _rebuildr_materialize_impl,
    # executable = True,
    attrs = {
        "src": attr.label(
            doc = "The rebuildr_image target to materialize",
            providers = [RebuildrInfo],
            mandatory = True,
        ),
        "_rebuildr_tool": attr.label(
            default = Label("//rebuildr:rebuildr"),
            executable = True, 
            cfg = "exec",
            doc = "The rebuildr executable",
        ),

    },
    doc = "Materializes a Docker image built by rebuildr_image",
)
