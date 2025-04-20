#!/usr/bin/env python3
"""
Smoke Test for Data Archive ML Synthesizer

This script performs a basic smoke test of the data-archive-ml-synthesizer project,
ensuring that the core components can be imported and executed without errors.
The test covers the key functionality of the pipeline, including:
- Loading data
- Building metadata
- Training a model
- Sampling synthetic data
- Reassembling XML
- Validating XML

No detailed assertions are made; the primary goal is to ensure the basic code
execution path is valid and no unhandled exceptions are raised.
"""

import logging
import os
import sys
import tempfile
from typing import Dict, Any

import pandas as pd

# Add the project root to the Python path to allow importing the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the main components from the package
from src.data_archive_ml_synthesizer.loader import DataLoader
from src.data_archive_ml_synthesizer.metadata_builder import MetadataBuilder
from src.data_archive_ml_synthesizer.model import GenerativeModel
from src.data_archive_ml_synthesizer.sampler import Sampler
from src.data_archive_ml_synthesizer.reassembler import XMLReassembler
from src.data_archive_ml_synthesizer.validator import XMLValidator
from src.data_archive_ml_synthesizer.pipeline import Pipeline, setup_logging


def setup_test_logging():
    """Set up logging for the smoke test."""
    logging.basicConfig(
        level=logging.DEBUG,  # Changed from INFO to DEBUG to see debug messages
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    # Suppress debug output from faker.factory
    logging.getLogger('faker.factory').setLevel(logging.INFO)
    return logging.getLogger('smoke_test')


def create_test_config():
    """Create a minimal configuration for testing."""
    # Use the existing input data files
    config = {
        'input': {
            'dmdsec_path': 'data/input/dmdSec.json',
            'file_path': 'data/input/file.json',
            'structmap_path': 'data/input/structMap.json',
        },
        'output': {
            'metadata_path': None,  # Will be set to a temporary file
            'model_path': None,     # Will be set to a temporary file
            'xml_output_path': None,  # Will be set to a temporary file
            'synthetic_data_paths': {
                'dmdSec': None,     # Will be set to a temporary file
                'file': None,       # Will be set to a temporary file
                'structMap': None,  # Will be set to a temporary file
            }
        },
        'model': {
            'type': 'multi_table',
            'random_seed': 42
        },
        'sampling': {
            'num_rows': {
                'dmdSec': 2,
                'file': 2,
                'structMap': 2
            }
        },
        'validation': {
            'enabled': True,
            'schema_paths': {
                'mets': 'schemas/mets.xsd',
                'dc': 'schemas/dc.xsd'
            }
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }

    # Create temporary directory for output files
    temp_dir = tempfile.mkdtemp()

    # Set temporary output paths
    config['output']['metadata_path'] = os.path.join(temp_dir, 'metadata.yaml')
    config['output']['model_path'] = os.path.join(temp_dir, 'model.pkl')
    config['output']['xml_output_path'] = os.path.join(temp_dir, 'synthetic_mets.xml')
    config['output']['synthetic_data_paths']['dmdSec'] = os.path.join(temp_dir, 'synthetic_dmdSec.json')
    config['output']['synthetic_data_paths']['file'] = os.path.join(temp_dir, 'synthetic_file.json')
    config['output']['synthetic_data_paths']['structMap'] = os.path.join(temp_dir, 'synthetic_structMap.json')

    return config, temp_dir


def test_data_loader(config: Dict[str, Any], logger: logging.Logger):
    """Test the DataLoader component."""
    logger.info("Testing DataLoader...")
    try:
        data_loader = DataLoader(config)
        dmdsec_df, file_df, structmap_df = data_loader.load_data()
        logger.info(f"Successfully loaded data: dmdSec ({len(dmdsec_df)} rows), "
                   f"file ({len(file_df)} rows), structMap ({len(structmap_df)} rows)")

        # Debug: Print column names to check for case sensitivity or other issues
        logger.info(f"dmdSec columns: {list(dmdsec_df.columns)}")
        logger.info(f"file columns: {list(file_df.columns)}")
        logger.info(f"structMap columns: {list(structmap_df.columns)}")

        return dmdsec_df, file_df, structmap_df
    except Exception as e:
        logger.error(f"Error in DataLoader: {str(e)}")
        raise


def test_metadata_builder(config: Dict[str, Any], dmdsec_df: pd.DataFrame, 
                         file_df: pd.DataFrame, structmap_df: pd.DataFrame, 
                         logger: logging.Logger):
    """Test the MetadataBuilder component."""
    logger.info("Testing MetadataBuilder...")
    try:
        metadata_builder = MetadataBuilder(config)
        metadata = metadata_builder.build_metadata(dmdsec_df, file_df, structmap_df)
        logger.info("Successfully built metadata")

        # Debug: Print metadata structure to check for issues
        logger.info(f"Metadata tables: {list(metadata['tables'].keys())}")
        for table_name, table_meta in metadata['tables'].items():
            logger.info(f"Table {table_name} metadata: primary_key={table_meta.get('primary_key')}, fields={list(table_meta.get('fields', {}).keys())}")

        return metadata
    except Exception as e:
        logger.error(f"Error in MetadataBuilder: {str(e)}")
        raise


def test_model(config: Dict[str, Any], tables: Dict[str, pd.DataFrame], 
              metadata: Dict[str, Any], logger: logging.Logger):
    """Test the GenerativeModel component."""
    logger.info("Testing GenerativeModel...")
    try:
        model = GenerativeModel(config)
        model.train(tables, metadata)
        logger.info("Successfully trained model")
        return model
    except Exception as e:
        logger.error(f"Error in GenerativeModel: {str(e)}")
        raise


def test_sampler(config: Dict[str, Any], model: GenerativeModel, logger: logging.Logger):
    """Test the Sampler component."""
    logger.info("Testing Sampler...")
    try:
        sampler = Sampler(config, model)
        synthetic_data = sampler.sample()
        logger.info(f"Successfully sampled synthetic data for {len(synthetic_data)} tables")
        return synthetic_data
    except Exception as e:
        logger.error(f"Error in Sampler: {str(e)}")
        raise


def test_reassembler(config: Dict[str, Any], synthetic_data: Dict[str, pd.DataFrame], 
                    logger: logging.Logger):
    """Test the XMLReassembler component."""
    logger.info("Testing XMLReassembler...")
    try:
        reassembler = XMLReassembler(config)
        xml_output_path = config.get('output', {}).get('xml_output_path')
        xml_root = reassembler.reassemble(synthetic_data, xml_output_path)
        logger.info(f"Successfully reassembled XML and saved to {xml_output_path}")
        return xml_root, xml_output_path
    except Exception as e:
        logger.error(f"Error in XMLReassembler: {str(e)}")
        raise


def test_validator(config: Dict[str, Any], xml_output_path: str, logger: logging.Logger):
    """Test the XMLValidator component."""
    logger.info("Testing XMLValidator...")
    try:
        validator = XMLValidator(config)
        is_valid, error_messages = validator.validate(xml_output_path, detailed_output=True)
        if is_valid:
            logger.info("XML validation succeeded")
        else:
            logger.warning("XML validation failed with the following errors:")
            for error in error_messages:
                logger.warning(f"  - {error}")
        return is_valid
    except Exception as e:
        logger.error(f"Error in XMLValidator: {str(e)}")
        raise


def test_pipeline(config: Dict[str, Any], logger: logging.Logger):
    """Test the entire Pipeline."""
    logger.info("Testing Pipeline...")
    try:
        pipeline = Pipeline(config)
        pipeline.run()
        logger.info("Pipeline executed successfully")
    except Exception as e:
        logger.error(f"Error in Pipeline: {str(e)}")
        raise


def run_smoke_test():
    """Run the smoke test for all components."""
    logger = setup_test_logging()
    logger.info("Starting smoke test for data-archive-ml-synthesizer")

    try:
        # Create test configuration
        config, temp_dir = create_test_config()
        logger.info(f"Created test configuration with temporary directory: {temp_dir}")

        # Set up logging based on the configuration
        setup_logging(config)

        # Test individual components
        dmdsec_df, file_df, structmap_df = test_data_loader(config, logger)

        tables = {
            'dmdSec': dmdsec_df,
            'file': file_df,
            'structMap': structmap_df
        }

        metadata = test_metadata_builder(config, dmdsec_df, file_df, structmap_df, logger)
        model = test_model(config, tables, metadata, logger)
        synthetic_data = test_sampler(config, model, logger)
        xml_root, xml_output_path = test_reassembler(config, synthetic_data, logger)
        test_validator(config, xml_output_path, logger)

        # Test the entire pipeline
        logger.info("Testing the entire pipeline...")
        test_pipeline(config, logger)

        logger.info("SMOKE TEST COMPLETED SUCCESSFULLY")
        print("SMOKE TEST COMPLETED SUCCESSFULLY")
        return 0
    except Exception as e:
        logger.error(f"Smoke test failed: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(run_smoke_test())
