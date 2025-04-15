"""
Module for testing the Minimum Viable Product (MVP) functionality of the METS XML synthesis pipeline.

This module provides a standalone script to test the core functionality of the pipeline:
- Loading configuration and input data
- Building metadata for SDV
- Training a generative model
- Sampling synthetic data
- Reassembling the data into a valid METS XML document

This script is useful for quick testing and demonstration of the pipeline's capabilities
without running the full pipeline with all its components.
"""

import os
import sys
import json
from pathlib import Path
import logging
import pandas as pd
import yaml

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MVP-Test")

# Import the necessary classes
from data_archive_ml_synthesizer.model import GenerativeModel
from data_archive_ml_synthesizer.loader import DataLoader
from data_archive_ml_synthesizer.metadata_builder import MetadataBuilder
from data_archive_ml_synthesizer.reassembler import XMLReassembler


def get_project_root():
    """
    Determine and return the path to the project root directory.

    This function attempts to find the project root by looking for the config.yaml file
    in the current directory and up to 4 parent directories. If it can't find the config,
    it falls back to using heuristics based on the directory structure.

    Returns:
        Path: The path to the project root directory.
    """
    # Start with the script's directory
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))

    # Check for config.yaml in current and parent directories
    current_dir = script_dir
    for _ in range(4):  # Check up to 4 levels up
        if (current_dir / "config.yaml").exists():
            return current_dir
        current_dir = current_dir.parent

    # If we reach here, we couldn't find the config
    logger.warning("Could not find config.yaml - using the top-level directory")
    # Use a known top-level directory as fallback
    if '/src/' in str(script_dir):
        # If we're in a src directory, go up to the project root
        return Path(str(script_dir).split('/src/')[0])

    # Last resort: go up two directories from the script location
    return script_dir.parent.parent


def load_config():
    """
    Load configuration from the config.yaml file in the project root directory.

    This function first determines the project root using get_project_root(),
    then attempts to load the configuration from config.yaml in that directory.
    If it encounters an error, it logs detailed information to help with debugging.

    Returns:
        tuple: A tuple containing:
            - config (dict): The loaded configuration dictionary
            - project_root (Path): The path to the project root directory

    Raises:
        Exception: If the configuration file cannot be loaded
    """
    project_root = get_project_root()
    config_path = project_root / "config.yaml"

    logger.info(f"Looking for configuration at: {config_path}")

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config, project_root
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")

        # Try to print directory contents to help debug
        try:
            logger.info(f"Current directory: {os.getcwd()}")
            logger.info(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
            logger.info(f"Project root determined as: {project_root}")
            logger.info(f"Project root contents: {list(project_root.iterdir())}")
        except Exception as dir_error:
            logger.error(f"Error listing directories: {str(dir_error)}")

        raise



def load_data(config, project_root):
    """
    Load input data from JSON files based on configuration.

    This function loads the three required JSON files (dmdSec, file, structMap)
    from the paths specified in the configuration, relative to the project root.
    It converts each JSON file to a pandas DataFrame and returns them in a dictionary.

    Args:
        config (dict): The configuration dictionary containing input file paths
        project_root (Path): The path to the project root directory

    Returns:
        dict: A dictionary mapping table names to pandas DataFrames:
            - 'dmdSec': DataFrame containing descriptive metadata
            - 'file': DataFrame containing file information
            - 'structMap': DataFrame containing structural relationships

    Raises:
        FileNotFoundError: If any of the required input files are not found
        Exception: If there's an error loading or processing the input data
    """
    try:
        # Load data directly from files using project_root
        dmdsec_path = project_root / config['input']['dmdsec_path']
        file_path = project_root / config['input']['file_path']
        structmap_path = project_root / config['input']['structmap_path']

        logger.info(f"Loading data from: {dmdsec_path}, {file_path}, {structmap_path}")

        # Check if files exist
        for path, name in [(dmdsec_path, "dmdSec"), (file_path, "file"), (structmap_path, "structMap")]:
            if not path.exists():
                raise FileNotFoundError(f"{name} file not found at {path}")

        # Load JSON files
        with open(dmdsec_path, 'r') as f:
            dmdsec_data = json.load(f)
            dmdsec_df = pd.DataFrame(dmdsec_data)

        with open(file_path, 'r') as f:
            file_data = json.load(f)
            file_df = pd.DataFrame(file_data)

        with open(structmap_path, 'r') as f:
            structmap_data = json.load(f)
            structmap_df = pd.DataFrame(structmap_data)

        # Create tables dictionary
        tables = {
            'dmdSec': dmdsec_df,
            'file': file_df,
            'structMap': structmap_df
        }

        logger.info(f"Loaded {len(tables)} tables from input data")
        return tables
    except Exception as e:
        logger.error(f"Error loading input data: {str(e)}")
        raise


def main():
    """
    Main function that orchestrates the MVP test of the METS XML synthesis pipeline.

    This function performs the following steps:
    1. Loads configuration and determines the project root
    2. Loads input data from JSON files
    3. Initializes the generative model
    4. Creates metadata using MetadataBuilder
    5. Trains the model on the input data
    6. Generates synthetic data using the trained model
    7. Reassembles the synthetic data into a METS XML document
    8. Saves the XML document to the specified output path

    Each step is wrapped in a try-except block to handle errors gracefully
    and provide informative error messages.
    """
    # Load configuration and determine project root
    try:
        config, project_root = load_config()
        logger.info(f"Project root directory: {project_root}")
    except Exception:
        return

    # Load input data
    try:
        tables = load_data(config, project_root)
    except Exception:
        return

    # Define output directory
    output_path = project_root / config['output']['xml_output_path']
    output_dir = output_path.parent
    os.makedirs(output_dir, exist_ok=True)

    # Create output file path
    output_file = output_path

    logger.info("Initializing the generative model...")

    # Create model configuration from the loaded config
    model_config = {
        "model_type": config['model']['type'],
        "output_format": "xml",
        "random_seed": config['model']['random_seed']
    }

    # Create and configure the model
    try:
        model = GenerativeModel(config=model_config)
        logger.info("Model initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing model: {str(e)}")
        return

    # Use MetadataBuilder to create metadata
    try:
        # Extract DataFrames from tables dictionary
        dmdsec_df = tables['dmdSec']
        file_df = tables['file']
        structmap_df = tables['structMap']

        # Create MetadataBuilder instance
        metadata_builder = MetadataBuilder(config)

        # Build metadata using the builder
        metadata = metadata_builder.build_metadata(dmdsec_df, file_df, structmap_df)

        logger.info("Metadata created successfully using MetadataBuilder")
    except Exception as e:
        logger.error(f"Error creating metadata: {str(e)}")
        return

    logger.info("Training the model...")

    # Train the model with the tables and metadata
    try:
        model.train(tables=tables, metadata=metadata)
        logger.info("Model trained successfully")
    except Exception as e:
        logger.error(f"Error during model training: {str(e)}")
        return

    logger.info("Synthesizing data...")

    # Generate synthetic data
    try:
        synthesized_data = model.sample()
        logger.info("Data synthesized successfully")
    except Exception as e:
        logger.error(f"Error during data synthesis: {str(e)}")
        return

    logger.info("Reassembling synthetic data into XML...")

    # Use XMLReassembler to convert synthetic data to XML
    try:
        reassembler = XMLReassembler(config)
        xml_root = reassembler.reassemble(synthesized_data, str(output_file))
        logger.info("XML reassembly completed successfully")
    except Exception as e:
        logger.error(f"Error during XML reassembly: {str(e)}")
        return

    logger.info(f"Synthetic XML written to {output_file}")

    # Print the contents of the XML file for review
    logger.info("Contents of the generated XML file:")
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            xml_content = f.read()
            print(xml_content[:500] + "..." if len(xml_content) > 500 else xml_content)
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")

    logger.info("MVP functionality test completed successfully")


if __name__ == "__main__":
    main()
