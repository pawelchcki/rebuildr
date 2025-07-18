load("@bazel_skylib//lib:shell.bzl", "shell")
load("//bzl/rule:providers.bzl", "RebuildrInfo")


def _rebuildr_push_impl(ctx):
    """Implementation of the rebuildr_push rule."""
    rebuildr_info = ctx.attr.src[RebuildrInfo]
    output = ctx.actions.declare_file(ctx.label.name + ".pushed")
    
    command = """
    set -eux
    
    export REBUILDR_OVERRIDE_ROOT_DIR={work_dir}
    export BUILDX_CONFIG=$(mktemp -d)
    trap "rm -rf $BUILDX_CONFIG" EXIT

    # Run the rebuildr tool to push the image
    {rebuildr} load-py {descriptor} push-image | tee {output}
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
        execution_requirements = {"no-cache": "", "external": "", "no-remote": "", "no-sandbox": "1"},
        use_default_shell_env = True,
    )
        
    return [DefaultInfo(
        files = depset([output]),
    ),
    
    
    ]

rebuildr_push = rule(
    implementation = _rebuildr_push_impl,
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
    },
    doc = "Pushes a Docker image built by rebuildr_image to a registry",
)

