"""
Module for orchestrating the entire METS XML synthesis pipeline.

This module serves as the CLI entry point that orchestrates the entire process:
data loading, metadata building, model training, synthetic sampling, XML reassembly,
and XML validation. It loads configuration from a separate config.yaml file and
logs progress and errors using the built-in logging module.
"""

import argparse
import os
import logging
import sys
import time
from typing import Dict, Any

import yaml

from src.data_archive_ml_synthesizer.loader import DataLoader
from src.data_archive_ml_synthesizer.metadata_builder import MetadataBuilder
from src.data_archive_ml_synthesizer.model import GenerativeModel
from src.data_archive_ml_synthesizer.sampler import Sampler
from src.data_archive_ml_synthesizer.reassembler import XMLReassembler
from src.data_archive_ml_synthesizer.validator import XMLValidator


def setup_logging(config: Dict[str, Any]) -> None:
    """
    Set up the logging configuration.

    Args:
        config: Dictionary containing configuration parameters.
    """
    # Create a logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO'))
    log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = log_config.get('file')

    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )

    # Suppress debug output from faker.factory
    logging.getLogger('faker.factory').setLevel(logging.INFO)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to the configuration file.

    Returns:
        Dictionary containing configuration parameters.
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Error loading configuration from {config_path}: {str(e)}")
        sys.exit(1)


class Pipeline:
    """
    Class for orchestrating the entire METS XML synthesis pipeline.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Pipeline with configuration.

        Args:
            config: Dictionary containing configuration parameters.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    def run(self) -> None:
        """
        Run the entire pipeline.
        """
        start_time = time.time()
        self.logger.info("Starting METS XML synthesis pipeline")

        try:
            # Step 1: Load data
            data_loader = DataLoader(self.config)
            dmdsec_df, file_df, structmap_df = data_loader.load_data()

            # Step 2: Build metadata
            metadata_builder = MetadataBuilder(self.config)
            metadata = metadata_builder.build_metadata(dmdsec_df, file_df, structmap_df)

            # Step 3: Train model
            model = GenerativeModel(self.config)
            tables = {
                'dmdSec': dmdsec_df,
                'file': file_df,
                'structMap': structmap_df
            }
            model.train(tables, metadata)

            # Step 4: Sample synthetic data
            sampler = Sampler(self.config, model)
            synthetic_data = sampler.sample()

            # Step 5: Reassemble XML
            reassembler = XMLReassembler(self.config)
            xml_output_path = self.config.get('output', {}).get('xml_output_path')
            xml_root = reassembler.reassemble(synthetic_data, xml_output_path)

            # Step 6: Validate XML
            if self.config.get('validation', {}).get('enabled', True):
                validator = XMLValidator(self.config)
                if xml_output_path:
                    is_valid, error_messages = validator.validate(xml_output_path, detailed_output=True)
                else:
                    is_valid, error_messages = validator.validate_element(xml_root, detailed_output=True)

                if not is_valid:
                    self.logger.warning("XML validation failed with the following errors:")
                    for error in error_messages:
                        self.logger.warning(f"  - {error}")
                else:
                    self.logger.info("XML validation succeeded")

            elapsed_time = time.time() - start_time
            self.logger.info(f"Pipeline completed successfully in {elapsed_time:.2f} seconds")

        except Exception as e:
            elapsed_time = time.time() - start_time
            self.logger.error(f"Pipeline failed after {elapsed_time:.2f} seconds: {str(e)}", exc_info=True)
            raise


def main():
    """
    Main entry point for the CLI.
    """
    parser = argparse.ArgumentParser(description='METS XML Synthesis Pipeline')
    parser.add_argument('--config', '-c', type=str, default='config.yaml',
                        help='Path to configuration file (default: config.yaml)')
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Set up logging
    setup_logging(config)

    # Create and run pipeline
    try:
        pipeline = Pipeline(config)
        pipeline.run()
    except Exception as e:
        logging.error(f"Pipeline execution failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
