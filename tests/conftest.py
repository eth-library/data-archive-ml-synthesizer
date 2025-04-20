import os
import sys

import pytest

# Add the project root to the Python path to allow importing the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the create_test_config and setup_test_logging functions from smoke_test
from tests.smoke_test import create_test_config, setup_test_logging
from src.data_archive_ml_synthesizer.loader import DataLoader
from src.data_archive_ml_synthesizer.metadata_builder import MetadataBuilder
from src.data_archive_ml_synthesizer.model import GenerativeModel
from src.data_archive_ml_synthesizer.sampler import Sampler
from src.data_archive_ml_synthesizer.reassembler import XMLReassembler

# Change to project root directory for tests
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope="session")
def config():
    """
    Fixture that provides a test configuration.

    This fixture has session scope to avoid recreating the configuration for each test.
    """
    config, _ = create_test_config()
    return config

@pytest.fixture(scope="session")
def logger():
    """
    Fixture that provides a logger for tests.

    This fixture has session scope to avoid recreating the logger for each test.
    """
    return setup_test_logging()

@pytest.fixture(scope="module")
def dmdsec_df(config, logger):
    """
    Fixture that provides the dmdSec DataFrame.

    This fixture has module scope to avoid reloading the data for each test in the same module.

    Args:
        config: The test configuration
        logger: The test logger

    Returns:
        pandas.DataFrame: The dmdSec DataFrame
    """
    logger.info("Loading dmdSec DataFrame")
    data_loader = DataLoader(config)
    dmdsec_df, _, _ = data_loader.load_data()
    return dmdsec_df

@pytest.fixture(scope="module")
def file_df(config, logger):
    """
    Fixture that provides the file DataFrame.

    This fixture has module scope to avoid reloading the data for each test in the same module.

    Args:
        config: The test configuration
        logger: The test logger

    Returns:
        pandas.DataFrame: The file DataFrame
    """
    logger.info("Loading file DataFrame")
    data_loader = DataLoader(config)
    _, file_df, _ = data_loader.load_data()
    return file_df

@pytest.fixture(scope="module")
def structmap_df(config, logger):
    """
    Fixture that provides the structMap DataFrame.

    This fixture has module scope to avoid reloading the data for each test in the same module.

    Args:
        config: The test configuration
        logger: The test logger

    Returns:
        pandas.DataFrame: The structMap DataFrame
    """
    logger.info("Loading structMap DataFrame")
    data_loader = DataLoader(config)
    _, _, structmap_df = data_loader.load_data()
    return structmap_df

@pytest.fixture(scope="module")
def tables(dmdsec_df, file_df, structmap_df, logger):
    """
    Fixture that provides all tables as a dictionary.

    This fixture has module scope to match the DataFrame fixtures it depends on.

    Args:
        dmdsec_df: The dmdSec DataFrame
        file_df: The file DataFrame
        structmap_df: The structMap DataFrame
        logger: The test logger

    Returns:
        dict: A dictionary containing all three DataFrames
    """
    logger.info("Creating tables dictionary")
    return {
        'dmdSec': dmdsec_df,
        'file': file_df,
        'structMap': structmap_df
    }

@pytest.fixture(scope="module")
def metadata(config, dmdsec_df, file_df, structmap_df, logger):
    """
    Fixture that provides the metadata.

    This fixture has module scope since metadata building is computationally expensive
    and the result doesn't change within a test module.

    Args:
        config: The test configuration
        dmdsec_df: The dmdSec DataFrame
        file_df: The file DataFrame
        structmap_df: The structMap DataFrame
        logger: The test logger

    Returns:
        dict: The metadata dictionary for SDV
    """
    logger.info("Building metadata")
    metadata_builder = MetadataBuilder(config)
    return metadata_builder.build_metadata(dmdsec_df, file_df, structmap_df)

@pytest.fixture(scope="module")
def model(config, tables, metadata, logger):
    """
    Fixture that provides the trained model.

    This fixture has module scope since model training is computationally expensive
    and the result doesn't change within a test module.

    Args:
        config: The test configuration
        tables: The dictionary of DataFrames
        metadata: The metadata dictionary
        logger: The test logger

    Returns:
        GenerativeModel: The trained model
    """
    logger.info("Training model")
    model = GenerativeModel(config)
    model.train(tables, metadata)
    return model

@pytest.fixture(scope="function")
def synthetic_data(config, model, logger):
    """
    Fixture that provides the synthetic data.

    This fixture has function scope to ensure fresh synthetic data for each test,
    since sampling is stochastic even with a fixed seed.

    Args:
        config: The test configuration
        model: The trained model
        logger: The test logger

    Returns:
        dict: A dictionary containing synthetic DataFrames
    """
    logger.info("Sampling synthetic data")
    sampler = Sampler(config, model)
    return sampler.sample()

@pytest.fixture(scope="function")
def xml_output_path(config, synthetic_data, logger):
    """
    Fixture that provides the XML output path.

    This fixture has function scope to ensure a fresh XML file for each test.

    Args:
        config: The test configuration
        synthetic_data: The synthetic data
        logger: The test logger

    Returns:
        str: The path to the generated XML file
    """
    logger.info("Reassembling XML")
    reassembler = XMLReassembler(config)
    xml_output_path = config.get('output', {}).get('xml_output_path')
    reassembler.reassemble(synthetic_data, xml_output_path)
    return xml_output_path
