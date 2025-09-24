#!/bin/sh

# shell get current script path https://stackoverflow.com/questions/4774054/reliable-way-for-a-bash-script-to-get-the-full-path-to-itself
SCRIPTPATH="$(
  cd -- "$(dirname "$0")" >/dev/null 2>&1
  pwd -P
)"

# detect if python3 or python is available
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BINARY="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BINARY="python"
else
  echo "Error: python3 or python is not installed"
  exit 1
fi

_REBUILDR_IMPL_DIR=$SCRIPTPATH/rebuildr_impl

if [ -n "$REBUILDR_SRC_DIR" ]; then
  _REBUILDR_IMPL_DIR=$REBUILDR_SRC_DIR
fi

PYTHONPATH=$_REBUILDR_IMPL_DIR $PYTHON_BINARY -m rebuildr.cli "$@"
