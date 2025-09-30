load("@bazel_skylib//lib:shell.bzl", "shell")
load("//bzl/rule:derive.bzl", "build_args_string", "env_declarations_string")
load("//bzl/rule:providers.bzl", "RebuildrInfo")

def _rebuildr_materialize_impl(ctx):
    rebuildr_info = ctx.attr.src[RebuildrInfo]

    output = ctx.actions.declare_file(ctx.label.name + ".out")

    build_args = dict(rebuildr_info.build_args)
    build_env = dict(rebuildr_info.build_env)

    build_args_arg = build_args_string(build_args)
    env_declarations = env_declarations_string(build_env)

    command = """
    set -o pipefail
    export REBUILDR_OVERRIDE_ROOT_DIR={work_dir}
    # verify registry can be reached - to quickly provide feedback if the registry is not reachable
    
    if ! {rebuildr} load-py {descriptor} {build_args_arg} check-target-registry-reachability; then
        echo "Registry is not reachable, check your internet/VPN connection and try again"
        exit 1
    fi

    # hack: rebuildr will copy files from $HOME to the new BUILDX_CONFIG directory to avoid not being able to write txn id
    export BUILDX_CONFIG=$(mktemp -d)
    trap "rm -rf $BUILDX_CONFIG" EXIT
    export _REBUILDR_HACK_BAZEL=1

    {env_declarations}

    # Run the rebuildr tool to materialize the image
    {rebuildr} load-py {descriptor} {build_args_arg} materialize-image  | tee {output}

    """.format(
        rebuildr = shell.quote(ctx.executable._rebuildr_tool.path),
        build_args_arg = build_args_arg,
        env_declarations = env_declarations,
        descriptor = shell.quote(rebuildr_info.descriptor.path),
        work_dir = shell.quote(rebuildr_info.work_dir.path),
        output = shell.quote(output.path),
    )

    ctx.actions.run_shell(
        inputs = [rebuildr_info.work_dir],
        outputs = [output],
        command = command,
        env = rebuildr_info.build_env,
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
