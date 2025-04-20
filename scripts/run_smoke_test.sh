#!/bin/bash
# Run the smoke test for the Data Archive ML Synthesizer project

# Change to the project root directory
cd "$(dirname "$0")/.." || exit 1

# Run the smoke test using pytest
echo "Running smoke test..."
python -m pytest tests/smoke_test.py -v

# Check the exit code
if [ $? -eq 0 ]; then
    echo "Smoke test passed!"
    exit 0
else
    echo "Smoke test failed!"
    exit 1
fi