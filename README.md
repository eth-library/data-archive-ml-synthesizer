# METS XML Synthesis Pipeline

A generative AI pipeline for synthesizing structured METS XML data based on real-world METS XML documents. This project uses SDV (Synthetic Data Vault) to produce reproducible synthetic test datasets for XML-based structured data.

## Overview

This pipeline takes flattened JSON representations of METS XML documents as input, trains a generative model on this data, and produces synthetic METS XML documents that maintain the structure and relationships of the original data while containing entirely synthetic content.

The pipeline follows a hybrid approach:
- The structure of the XML (tags, hierarchy, schema) is defined using XML templates
- The content inside the tags (titles, dates, agent names, mimetypes) is generated using generative machine learning (via SDV)
- These values are inserted into predefined XML templates to guarantee schema compliance and structural validity

## Project Structure

```
data-archive-ml-synthesizer/
├── config.yaml                # Configuration file
├── README.md                  # This file
├── pyproject.toml             # Project metadata and dependencies (PEP 621)
├── poetry.lock                # Poetry lock file for dependency management
├── poetry.toml                # Poetry configuration
├── flake.nix                  # Nix flake configuration
├── flake.lock                 # Nix flake lock file
├── main.py                    # Main entry point
├── src/                       # Source code
│   └── data_archive_ml_synthesizer/  # Main package
│       ├── __init__.py        # Package initialization
│       ├── loader.py          # Data loading module
│       ├── metadata_builder.py # Metadata construction
│       ├── model.py           # Model implementation
│       ├── pipeline.py        # Pipeline orchestration
│       ├── reassembler.py     # XML reassembly
│       ├── sampler.py         # Synthetic data sampling
│       ├── validator.py       # XML validation
│       └── test_mvp.py        # MVP test script
├── tests/                     # Test directory
│   ├── README.md              # Test documentation
│   ├── conftest.py            # Test configuration
│   └── smoke_test.py          # Smoke test script
├── scripts/                   # Utility scripts
│   └── run_smoke_test.sh      # Script to run smoke test
├── data/                      # Data directory
│   ├── input/                 # Input JSON files
│   │   ├── dmdSec.json        # Descriptive metadata
│   │   ├── file.json          # File information
│   │   └── structMap.json     # Structural relationships
│   └── output/                # Output files
│       ├── metadata.yaml      # Generated SDV metadata
│       └── synthetic_mets.xml # Synthetic METS XML
├── schemas/                   # XML schemas
│   ├── mets.xsd               # METS schema
│   ├── dc.xsd                 # Dublin Core schema
└── logs/                      # Log files
    └── pipeline.log           # Pipeline execution log
```

## Core Tools and Dependencies

This project relies on several key libraries and tools to accomplish its data synthesis tasks:

### SDV (Synthetic Data Vault)

SDV is the core machine learning framework used in this project for generating synthetic data. We use it to:

- Create and train generative models on our structured data
- Generate synthetic data that maintains the statistical properties and relationships of the original data
- Preserve referential integrity between related tables (dmdSec, file, structMap)

We specifically use the HMASynthesizer (Hierarchical Multi-table Approach) from SDV, which is designed to handle hierarchical relationships between tables while preserving their statistical properties.

### pandas and DataFrames

pandas is essential to our data manipulation workflow:

- Input JSON data is converted to pandas DataFrames for efficient processing
- DataFrames serve as the common data structure throughout the pipeline
- We leverage pandas for data cleaning, transformation, and validation
- The synthetic data is generated as DataFrames before being converted back to XML

pandas provides the flexibility to handle complex data transformations and the performance needed for larger datasets.

### XML Processing Tools

For XML handling, we use:

- lxml: For creating, manipulating, and serializing XML documents
- xmlschema: For validating the generated XML against XSD schemas

These tools ensure that our synthetic METS XML documents are well-formed and valid according to the METS, Dublin Core, and DNX schemas.

## Environment Setup

### Prerequisites

- [Nix](https://nixos.org/download.html) with flakes enabled
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management

### Setting Up with Nix Flakes

This project uses Nix flakes to provide a fully reproducible development environment. The development shell includes system dependencies and Poetry, which automatically creates a Python virtual environment (.venv) in the project root and installs all dependencies.

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/data-archive-ml-synthesizer.git
   cd data-archive-ml-synthesizer
   ```

2. Enable Nix flakes (if not already enabled):

   Add the following to your `~/.config/nix/nix.conf` or `/etc/nix/nix.conf`:
   ```
   experimental-features = nix-command flakes
   ```

3. Enter the development environment:
   ```bash
   nix develop
   ```

   This command creates a shell with:
   - Python 3.12 interpreter
   - Poetry for dependency management
   - System dependencies (libxml2, libxslt, zlib, etc.)
   - A local virtual environment (.venv) for IDE integration (automatically created and activated)
   - The necessary directories (`data/input`, `data/output`, `schemas`, `logs`) will be created automatically

   The shellHook automatically:
   - Configures Poetry to use in-project virtual environments
   - Runs `poetry install` to install all dependencies
   - Activates the virtual environment

4. Place your input JSON files in the `data/input` directory and XML schemas in the `schemas` directory.

### Dependency Management

This project uses modern Python packaging standards:

- **pyproject.toml**: Defines project metadata and dependencies according to PEP 621
- **Poetry**: Manages Python dependencies and virtual environments
- **Virtual Environment**: A local .venv is created for IDE integration and developer flexibility

The system is designed to be flexible:
- For Nix users: System dependencies and Poetry are managed reproducibly through the flake.nix
- For Python developers: Poetry manages Python dependencies in the local .venv
- For CI/CD: The exact same environment can be reproduced on any system with Nix

### Using the Environment

Once inside the Nix development shell, you can run project commands directly:

```bash
# Run the pipeline
python -m src.pipeline

# Run all tests
pytest tests/

# Run the smoke test
./scripts/run_smoke_test.sh

# Or run the smoke test directly
pytest tests/smoke_test.py -v

# Run with a custom configuration
python -m src.pipeline --config custom_config.yaml
```

## Testing

The project includes a smoke test that verifies the basic functionality of the pipeline. The smoke test:

- Imports all the main modules
- Instantiates key classes
- Calls primary functions with minimal valid inputs
- Verifies that no unhandled exceptions are raised

### Running the Smoke Test

You can run the smoke test in several ways:

1. Using the convenience script:
   ```bash
   ./scripts/run_smoke_test.sh
   ```

2. Using pytest directly:
   ```bash
   pytest tests/smoke_test.py -v
   ```

3. Running the script directly:
   ```bash
   ./tests/smoke_test.py
   ```

The smoke test uses the existing input data files but creates temporary output files to avoid modifying the project's output directory.

### Using with direnv (Optional)

For an even smoother workflow, you can use [direnv](https://direnv.net/) to automatically enter the development environment when you navigate to the project directory:

1. Install direnv following the instructions at https://direnv.net/
2. Create a `.envrc` file in the project root with the content:
   ```
   use flake
   ```
3. Allow direnv to use this configuration:
   ```bash
   direnv allow
   ```

Now the environment will be automatically activated when you enter the project directory and deactivated when you leave. The shellHook will automatically configure Poetry, install dependencies, and activate the virtual environment.

#### Troubleshooting direnv with Nix Flakes

If you encounter an error when using direnv, try:
- Running `git add .` to stage your changes (addressing any "dirty" warnings)
- Running `nix flake update` to refresh the lock file
- Deleting the `.direnv` directory and running `direnv allow` again

> **Note**: The flake.nix creates and manages a .venv for you using Poetry. This approach gives you the reproducibility of Nix for system dependencies with the flexibility of Poetry for Python dependency management.

## Configuration

The pipeline is configured through the `config.yaml` file. Key configuration options include:

- **Input/Output Paths**: Locations of input JSON files and output files
- **Model Type**: Choose between `hma1` (individual table models) or `multi_table` (MultiTableSynthesizer)
- **Sampling Parameters**: Number of rows to generate for each table
- **Validation Settings**: XSD schema paths for validation
- **Logging Configuration**: Log level, format, and output file

See the comments in `config.yaml` for detailed descriptions of each option.

## Usage

### Running the Pipeline

To run the pipeline with the default configuration:

```bash
python -m src.pipeline
```

To specify a different configuration file:

```bash
python -m src.pipeline --config custom_config.yaml
```

### Pipeline Steps

1. **Data Loading**: Load and validate the three JSON files (dmdSec, file, structMap)
2. **Metadata Construction**: Build SDV-compatible metadata describing tables and relationships
3. **Model Training**: Train a generative model on the input data
4. **Data Sampling**: Generate synthetic data for each table
5. **XML Reassembly**: Convert synthetic data back into a valid METS XML document
6. **XML Validation**: Validate the generated XML against XSD schemas

## Architecture

### Module Descriptions

- **loader.py**: Loads input JSON files and performs basic validation of their structure
- **metadata_builder.py**: Builds SDV-compatible metadata describing tables and relationships
- **model.py**: Implements a factory pattern to create and train different types of SDV models
- **sampler.py**: Handles sampling synthetic data from trained models
- **reassembler.py**: Converts synthetic data back into valid METS XML with proper structure
- **validator.py**: Validates generated XML against XSD schemas
- **pipeline.py**: Orchestrates the entire process and provides CLI interface

### Data Processing Pipeline

The pipeline follows these key steps:

1. **Data Gathering and Parsing**: 
   - Input data is provided as flattened JSON files representing METS XML components
   - The loader module parses these files and converts them to pandas DataFrames
   - Basic validation ensures the required columns and relationships are present

2. **Data Cleaning and Preparation**:
   - Foreign key relationships are validated to ensure referential integrity
   - Data types are inferred and standardized for machine learning compatibility
   - Metadata is constructed to describe the tables, their columns, and relationships

3. **Model Training**:
   - The HMASynthesizer from SDV is trained on the prepared data
   - This model learns the statistical properties and relationships in the data
   - Training uses a fixed random seed for reproducibility

4. **Synthetic Data Generation**:
   - The trained model generates new synthetic data that preserves the learned patterns
   - The number of rows to generate for each table is configurable
   - Post-processing ensures the synthetic data maintains referential integrity

5. **XML Reassembly**:
   - The synthetic data is converted back into a valid METS XML document
   - XML templates ensure proper structure and namespaces
   - The reassembly process maintains relationships between XML elements

6. **Validation and Output**:
   - The generated XML is validated against XSD schemas
   - The final METS XML document is saved to the specified output path

### Machine Learning Methods

This project employs several machine learning techniques through the SDV framework:

#### Hierarchical Multi-table Approach (HMA)

The core of our synthetic data generation is the HMASynthesizer from SDV, which:

- Uses a hierarchical approach to model relationships between tables
- Learns the statistical distributions of each column
- Captures correlations between columns within and across tables
- Preserves primary key-foreign key relationships

#### Statistical Modeling

The underlying statistical methods include:

- Gaussian copulas for modeling correlations between numerical variables
- Categorical variable modeling using frequency-based approaches
- Bayesian networks for capturing conditional dependencies
- Gaussian mixture models for complex distributions

The machine learning process is fully automated, with the SDV framework handling the selection and tuning of appropriate models for each data type and relationship.

### Data Flow

```
Input JSON Files → Metadata Construction → Model Training → Synthetic Data Sampling → XML Reassembly → XML Validation → Output XML
```

## Testing and Debugging

### Running Tests

The project includes a comprehensive test suite for the non-ML components of the pipeline. To run the tests:

```bash
# Run all tests (pytest is already installed in the development environment)
pytest tests/

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

For more details on the test suite, see the [tests/README.md](tests/README.md) file.

### Debugging

The pipeline includes logging at various levels to help with debugging. To enable more detailed logging, set the `level` parameter in the `logging` section of `config.yaml` to `DEBUG`.

### Common Issues

- **Missing Input Files**: Ensure all required JSON files are present in the specified input directory
- **Schema Validation Errors**: Check that the generated XML conforms to the provided schemas
- **Model Training Failures**: May occur with insufficient or inconsistent input data

### Reproducibility

The pipeline uses a fixed random seed (configurable in `config.yaml`) to ensure reproducible results. This means that running the pipeline multiple times with the same input data and configuration should produce identical synthetic data.
