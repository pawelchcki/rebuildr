#!/bin/sh

# tar to stdout
ROOT_DIR="$(
  cd -- "$(dirname "$0")"/.. >/dev/null 2>&1
  pwd -P
)"

cd $ROOT_DIR/dist

tar -cf - .
