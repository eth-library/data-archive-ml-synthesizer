"""
Module for building SDV-compatible metadata.

This module provides functionality to build metadata for SDV 1.20.0,
defining the relationships between the three tables:
- dmdSec: Primary key dmd_id
- file: Primary key file_id and a foreign key dmd_id referencing dmdSec
- structMap: Primary key struct_id with a foreign key dmd_id referencing dmdSec
  and a self-referencing key parent_id (for hierarchical structure)
"""

import logging
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import yaml

from sdv.metadata import Metadata


class MetadataBuilder:
    """
    Class for building SDV-compatible metadata using SDV 1.20.0's Metadata API.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the MetadataBuilder with configuration.

        Args:
            config: Dictionary containing configuration parameters.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    def build_metadata(self, dmdsec_df: pd.DataFrame, file_df: pd.DataFrame, 
                      structmap_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Build SDV-compatible metadata for the three tables using SDV 1.20.0's Metadata API.

        Args:
            dmdsec_df: DataFrame containing dmdSec data.
            file_df: DataFrame containing file data.
            structmap_df: DataFrame containing structMap data.

        Returns:
            Dictionary containing SDV-compatible metadata.
        """
        self.logger.info("Building metadata for SDV...")

        # Create a dictionary of tables
        tables = {
            'dmdSec': dmdsec_df,
            'file': file_df,
            'structMap': structmap_df
        }

        # Log table details
        for table_name, df in tables.items():
            self.logger.debug(f"Table '{table_name}' data: {len(df)} rows, columns={list(df.columns)}")

        # First, create metadata with just the tables and their columns
        metadata_obj = Metadata()

        # Add tables and set primary keys
        for table_name, df in tables.items():
            metadata_obj.add_table(table_name)

            # Add columns with appropriate types
            for column in df.columns:
                if column.endswith('_id'):
                    metadata_obj.add_column(column, table_name, sdtype='id')
                elif 'date' in column.lower():
                    metadata_obj.add_column(column, table_name, sdtype='datetime')
                elif pd.api.types.is_numeric_dtype(df[column].dtype):
                    metadata_obj.add_column(column, table_name, sdtype='numerical')
                else:
                    metadata_obj.add_column(column, table_name, sdtype='categorical')

            # Set primary keys
            if table_name == 'dmdSec':
                metadata_obj.set_primary_key('dmd_id', table_name)
            elif table_name == 'file':
                metadata_obj.set_primary_key('file_id', table_name)
            elif table_name == 'structMap':
                metadata_obj.set_primary_key('struct_id', table_name)

        # Add relationships manually
        # dmdSec to file relationship
        metadata_obj.add_relationship(
            parent_table_name='dmdSec',
            parent_primary_key='dmd_id',
            child_table_name='file',
            child_foreign_key='dmd_id'
        )

        # dmdSec to structMap relationship
        metadata_obj.add_relationship(
            parent_table_name='dmdSec',
            parent_primary_key='dmd_id',
            child_table_name='structMap',
            child_foreign_key='dmd_id'
        )

        # Note: We're not adding the structMap self-referencing relationship
        # because it creates a circular dependency that SDV can't handle.
        # The parent_id column is still in the data and will be preserved,
        # but it won't be treated as a foreign key in the metadata.

        # Validate the metadata
        metadata_obj.validate()

        # Convert to dictionary
        metadata_dict = metadata_obj.to_dict()

        # Save metadata to file if specified in config
        if 'metadata_path' in self.config['output']:
            metadata_path = Path(self.config['output']['metadata_path'])
            self._save_metadata(metadata_dict, metadata_path)

        self.logger.info("Metadata built successfully.")
        return metadata_dict

    def _save_metadata(self, metadata: Dict[str, Any], file_path: Path) -> None:
        """
        Save metadata to a YAML file.

        Args:
            metadata: Metadata dictionary to save.
            file_path: Path where to save the metadata.
        """
        self.logger.debug(f"Saving metadata to {file_path}")

        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, 'w') as f:
                yaml.dump(metadata, f, default_flow_style=False)

            self.logger.info(f"Metadata saved to {file_path}")

        except Exception as e:
            error_msg = f"Error saving metadata to {file_path}: {str(e)}"
            self.logger.error(error_msg)
            raise
