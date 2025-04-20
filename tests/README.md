# Test Suite Documentation

## Test Suite Overview

This directory contains the test suite for the METS XML Synthesis Pipeline. The tests are designed to verify the functionality of the pipeline components and ensure that they work together correctly. The test suite provides comprehensive coverage of the pipeline's functionality, from data loading to XML validation.

## Test Structure

The test suite consists of:

- `conftest.py`: Contains pytest fixtures that set up the test environment
- `smoke_test.py`: A comprehensive smoke test that verifies the basic functionality of all pipeline components

The smoke test includes individual test functions for each component of the pipeline:

1. `test_data_loader`: Tests the loading and validation of input JSON files
2. `test_metadata_builder`: Tests the construction of SDV-compatible metadata
3. `test_model`: Tests the training of a generative model
4. `test_sampler`: Tests the generation of synthetic data
5. `test_reassembler`: Tests the conversion of synthetic data to XML
6. `test_validator`: Tests the validation of the generated XML
7. `test_pipeline`: Tests the end-to-end pipeline execution

## Fixtures

The test fixtures in `conftest.py` are designed to provide reusable components for tests. They follow a dependency chain that mirrors the pipeline's execution flow:

### Core Fixtures

- `config` (session scope): Provides a test configuration with temporary output paths
- `logger` (session scope): Provides a logger for tests

### Data Fixtures

- `dmdsec_df`, `file_df`, `structmap_df` (module scope): Provide the input DataFrames
- `tables` (module scope): Combines the DataFrames into a dictionary

### Processing Fixtures

- `metadata` (module scope): Builds metadata from the input DataFrames
- `model` (module scope): Trains a model on the input data
- `synthetic_data` (function scope): Generates synthetic data from the model
- `xml_output_path` (function scope): Reassembles the synthetic data into XML

The fixtures use different scopes to optimize test execution:

- **Session scope**: Created once per test session (e.g., `config`, `logger`)
- **Module scope**: Created once per test module (e.g., `dmdsec_df`, `metadata`, `model`)
- **Function scope**: Created for each test function (e.g., `synthetic_data`, `xml_output_path`)

## Running Tests

To run the smoke test:

```bash
# Run with pytest (recommended)
pytest tests/smoke_test.py -v

# Or run the script directly
./tests/smoke_test.py
```

To run a specific test function:

```bash
pytest tests/smoke_test.py::test_data_loader -v
```

To run all tests with detailed output:

```bash
pytest tests/ -v
```

### Testing vs. Production Usage

Understanding the difference between testing and production usage is important:

| Aspect | Testing (pytest) | Production |
|--------|-----------------|------------|
| **Entry Point** | `pytest tests/smoke_test.py` | `python -m src.data_archive_ml_synthesizer.pipeline` |
| **Configuration** | Test configuration created in `conftest.py` | Configuration from `config.yaml` |
| **Output Files** | Temporary files | Files specified in `config.yaml` |
| **Purpose** | Verify code functionality | Generate synthetic METS XML |
| **Environment** | Test fixtures automatically set up | Manual configuration required |

When to use each approach:
- Use **pytest** during development to verify that your code changes don't break existing functionality
- Use **production mode** when you want to generate actual synthetic METS XML documents for your use case

## Writing New Tests

When writing new tests, you can use the fixtures defined in `conftest.py` to set up the test environment. For example:

```python
def test_example(config, synthetic_data, logger):
    """Example test using fixtures."""
    # Your test code here
    assert synthetic_data is not None
```

The fixtures will be automatically created and injected into your test function.

### Best Practices for Writing Tests

1. **Use fixtures**: Leverage the existing fixtures to set up the test environment
2. **Test one thing at a time**: Each test function should focus on testing a single aspect of the code
3. **Use descriptive names**: Test function names should clearly describe what they're testing
4. **Include assertions**: Every test should include at least one assertion to verify the expected behavior
5. **Handle exceptions**: Use pytest's exception handling to test for expected exceptions

## Test Configuration

The test configuration is created in `conftest.py` using the `create_test_config()` function from `smoke_test.py`. It uses the same input files as the main configuration but creates temporary output paths to avoid modifying the project's output files.

The test configuration includes:
- Input paths pointing to the same input files as the main configuration
- Temporary output paths for generated files
- A fixed random seed for reproducibility
- Validation settings matching the main configuration
