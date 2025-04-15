"""
Module for training generative models using SDV.

This module implements a factory pattern to create and train an HMA synthesizer.
The HMA synthesizer uses a hierarchical machine learning algorithm to generate synthetic data.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

from sdv.metadata import Metadata
from sdv.multi_table.hma import HMASynthesizer
from sdv.utils import drop_unknown_references


class ModelFactory:
    """
    Factory class for creating and training an HMA synthesizer model.
    """

    @staticmethod
    def create_model(metadata: Dict[str, Any], config: Dict[str, Any]) -> HMASynthesizer:
        """
        Create an HMA synthesizer model.

        Args:
            metadata: SDV-compatible metadata as a dictionary.
            config: Configuration dictionary.

        Returns:
            An instance of HMASynthesizer.
        """
        logger = logging.getLogger(__name__)
        logger.info("Creating HMA model...")

        # Convert dictionary metadata to Metadata object
        sdv_metadata = Metadata.load_from_dict(metadata)

        # Instantiate the HMASynthesizer with the prepared metadata
        model = HMASynthesizer(metadata=sdv_metadata)
        logger.info("Created HMA model successfully.")

        return model


class GenerativeModel:
    """
    Class for training and sampling from the HMA synthesizer model.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the GenerativeModel with the configuration.

        Args:
            config: Dictionary containing configuration parameters.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.metadata = None

    def train(self, tables: Dict[str, pd.DataFrame], metadata: Dict[str, Any]) -> None:
        """
        Train the HMA synthesizer model on the input data.

        Args:
            tables: Dictionary mapping table names to DataFrames.
            metadata: SDV-compatible metadata as a dictionary.
        """
        self.logger.info("Training HMA synthesizer model...")
        self.metadata = metadata

        # Log table details
        for table_name, df in tables.items():
            self.logger.debug(f"Table '{table_name}' data: {len(df)} rows, columns={list(df.columns)}")

        # Clean data to ensure foreign keys reference valid primary keys
        cleaned_tables = drop_unknown_references(
            data=tables, 
            metadata=Metadata.load_from_dict(metadata)
        )
        self.logger.info("Cleaned tables to enforce referential integrity.")

        # Create the HMA model using the factory
        self.model = ModelFactory.create_model(metadata, self.config)

        # Train the synthesizer
        self.model.fit(cleaned_tables)
        self.logger.debug("model.fit completed successfully.")

        # Save the model if a model path is specified
        if 'model_path' in self.config.get('output', {}):
            self._save_model(Path(self.config['output']['model_path']))

        self.logger.info("Model training completed successfully.")

    def sample(self, num_rows: Optional[Dict[str, int]] = None) -> Dict[str, pd.DataFrame]:
        """
        Generate synthetic data using the trained HMA synthesizer model.

        Args:
            num_rows: Optional dictionary specifying the number of rows to generate for each table.
                      Defaults to using values from the configuration or 100 rows per table if not provided.

        Returns:
            Dictionary mapping table names to DataFrames containing synthetic data.

        Raises:
            ValueError: If the model has not been trained.
        """
        if self.model is None:
            raise ValueError("Model has not been trained. Please call train() first.")

        self.logger.info("Generating synthetic data...")
        if num_rows is None:
            num_rows = self.config.get('sampling', {}).get('num_rows', {})
            if not num_rows:
                num_rows = {table: 100 for table in self.metadata.get('tables', {}).keys()}

        # In SDV 1.20.0, the sample method doesn't accept num_rows parameter
        # Instead, we need to call sample() without parameters and then filter the results
        synthetic_data = self.model.sample()

        # Limit the number of rows in each table based on num_rows
        for table_name, count in num_rows.items():
            if table_name in synthetic_data and len(synthetic_data[table_name]) > count:
                synthetic_data[table_name] = synthetic_data[table_name].head(count)

        self.logger.info(f"Generated synthetic data for {len(synthetic_data)} tables.")
        return synthetic_data

    def _save_model(self, file_path: Path) -> None:
        """
        Save the trained model to a file.

        Args:
            file_path: Path where the model is to be saved.
        """
        self.logger.debug(f"Saving model to {file_path}")
        file_path.parent.mkdir(parents=True, exist_ok=True)

        self.model.save(file_path)
        self.logger.info(f"Model saved to {file_path}")
