FROM bash

WORKDIR /test
COPY . .

RUN set -xe; find . -type f

RUN set -xe; \
    test -f example_file.txt; \
    test -f ./test_example_bzl_deps/external_test_example_bzl_deps.txt; \
    test -f ./test_example_bzl_deps/external_subdir/file_in_subdir.txt; \
    test -f ./test_example_bzl_deps/external_generated_subfolder/file_in_subdir.txt; \
    test -f ./test_example_bzl_deps/external_generated_subfolder/external_test_example_bzl_deps.txt; \
    test -f ./test_example_bzl_deps.txt; \
    test -f ./generated_subfolder/file_in_subdir.txt; \
    test -f ./generated_subfolder/test_example_bzl_deps.txt; \
    test -f ./dependencies_mapping.Dockerfile; \
    test -f ./example_file.txt; \
    test -f ./subdir/file_in_subdir.txt;

# there should be exactly 10 files
RUN set -xe; \
    find . -type f | sort | wc -l | grep -q "10"