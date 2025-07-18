#!/bin/bash
set -xeuo pipefail

# Get the output file path from the arguments
OUTPUT_FILE="$1"
EXPECTED_OUTPUT="$2"

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

cat ${OUTPUT_FILE}

diff -uP "${EXPECTED_OUTPUT}" "${OUTPUT_FILE}"

echo "All tests passed!"
exit 0
