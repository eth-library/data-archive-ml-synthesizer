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

@pytest.fixture
def config():
    """Fixture that provides a test configuration."""
    config, _ = create_test_config()
    return config

@pytest.fixture
def logger():
    """Fixture that provides a logger for tests."""
    return setup_test_logging()

@pytest.fixture
def dmdsec_df(config, logger):
    """Fixture that provides the dmdSec DataFrame."""
    data_loader = DataLoader(config)
    dmdsec_df, _, _ = data_loader.load_data()
    return dmdsec_df

@pytest.fixture
def file_df(config, logger):
    """Fixture that provides the file DataFrame."""
    data_loader = DataLoader(config)
    _, file_df, _ = data_loader.load_data()
    return file_df

@pytest.fixture
def structmap_df(config, logger):
    """Fixture that provides the structMap DataFrame."""
    data_loader = DataLoader(config)
    _, _, structmap_df = data_loader.load_data()
    return structmap_df

@pytest.fixture
def tables(dmdsec_df, file_df, structmap_df):
    """Fixture that provides all tables as a dictionary."""
    return {
        'dmdSec': dmdsec_df,
        'file': file_df,
        'structMap': structmap_df
    }

@pytest.fixture
def metadata(config, dmdsec_df, file_df, structmap_df, logger):
    """Fixture that provides the metadata."""
    metadata_builder = MetadataBuilder(config)
    return metadata_builder.build_metadata(dmdsec_df, file_df, structmap_df)

@pytest.fixture
def model(config, tables, metadata, logger):
    """Fixture that provides the trained model."""
    model = GenerativeModel(config)
    model.train(tables, metadata)
    return model

@pytest.fixture
def synthetic_data(config, model, logger):
    """Fixture that provides the synthetic data."""
    sampler = Sampler(config, model)
    return sampler.sample()

@pytest.fixture
def xml_output_path(config, synthetic_data, logger):
    """Fixture that provides the XML output path."""
    reassembler = XMLReassembler(config)
    xml_output_path = config.get('output', {}).get('xml_output_path')
    reassembler.reassemble(synthetic_data, xml_output_path)
    return xml_output_path
