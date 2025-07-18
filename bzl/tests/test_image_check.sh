#!/bin/bash
set -euo pipefail

# Get the output file path from the arguments
OUTPUT_FILE="$1"

# Check if the output file exists
if [[ ! -f ${OUTPUT_FILE} ]]; then
  echo "ERROR: Output file ${OUTPUT_FILE} does not exist."
  exit 1
fi

# Check if the output file has content
if [[ ! -s ${OUTPUT_FILE} ]]; then
  echo "ERROR: Output file ${OUTPUT_FILE} is empty."
  exit 1
fi

# Check if output contains an image ID
if ! grep -q "^test-image:src-id-[a-f0-9]\+$" "${OUTPUT_FILE}"; then
  echo "ERROR: Output file does not contain expected image ID pattern."
  exit 1
fi

echo "All tests passed!"
exit 0
