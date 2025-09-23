workspace(name = "rebuildr")

# Python rules
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "rules_python",
    sha256 = "84aec9e21cc56fbc7f1335035a71c850d1b9b5cc6ff497306f84cced9a769841",
    strip_prefix = "rules_python-0.23.1",
    url = "https://github.com/bazelbuild/rules_python/releases/download/0.23.1/rules_python-0.23.1.tar.gz",
)

load("@rules_python//python:repositories.bzl", "py_repositories")

py_repositories()

# Skylib for shell utils
http_archive(
    name = "bazel_skylib",
    sha256 = "b8a1527901774180afc798aeb28c4634bdccf19c4d98e7bdd1ce79d1fe9aaad7",
    urls = [
        "https://mirror.bazel.build/github.com/bazelbuild/bazel-skylib/releases/download/1.4.1/bazel-skylib-1.4.1.tar.gz",
        "https://github.com/bazelbuild/bazel-skylib/releases/download/1.4.1/bazel-skylib-1.4.1.tar.gz",
    ],
)

load("@bazel_skylib//:workspace.bzl", "bazel_skylib_workspace")

bazel_skylib_workspace()

load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")

git_repository(
    name = "rules_oci_bootstrap",
    commit = "75330296a80c4a5bfa228dc585ca9a9c3e56d45d",
    remote = "https://github.com/DataDog/rules_oci_bootstrap.git",
)

# Datadog  Rules OCI for compatibility testing

load("@rules_oci_bootstrap//:defs.bzl", "oci_blob_pull")

oci_blob_pull(
    name = "com_github_datadog_rules_oci",
    digest = "sha256:cc6c59ed7da6bb376552461e06068f883bbe335359c122c15dce3c24e19cd8e2",
    extract = True,
    registry = "ghcr.io",
    repository = "datadog/rules_oci/rules",
    type = "tar.gz",
)

# Bazel contrib Rules OCI for compatibility testing

http_archive(
    name = "rules_oci",
    sha256 = "5994ec0e8df92c319ef5da5e1f9b514628ceb8fc5824b4234f2fe635abb8cc2e",
    strip_prefix = "rules_oci-2.2.6",
    url = "https://github.com/bazel-contrib/rules_oci/releases/download/v2.2.6/rules_oci-v2.2.6.tar.gz",
)

load("@rules_oci//oci:dependencies.bzl", "rules_oci_dependencies")

rules_oci_dependencies()

load("@rules_oci//oci:repositories.bzl", "oci_register_toolchains")

oci_register_toolchains(name = "oci")

local_repository(
    name = "test_example_bzl_deps",
    path = "bzl/test_example_bzl_deps/external_repository",
)
