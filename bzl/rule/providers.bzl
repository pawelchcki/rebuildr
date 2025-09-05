# Define a provider to share information between rebuildr_image and rebuildr_materialize and others

RebuildrInfo = provider(
    doc = "Information and data about a rebuildr image ",
    fields = {
        "descriptor": "The descriptor file used to define the image",
        "work_dir": "The directory containing the build context",
        "stable_file": "The stable output file",
        "stable_image_tag": "The stable image tag",
        "build_env": "The build environment variables",
        "build_args": "The build arguments",
    },
)
