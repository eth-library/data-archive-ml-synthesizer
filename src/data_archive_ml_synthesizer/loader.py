"""
Module for loading and validating input JSON files.

This module provides functionality to load the three JSON files
(dmdSec.json, file.json, structMap.json) and perform basic validation
of their structure.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple

import pandas as pd


class DataLoader:
    """
    Class for loading and validating input JSON data.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the DataLoader with configuration.

        Args:
            config: Dictionary containing configuration parameters including file paths.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load the three JSON files and convert them to pandas DataFrames.

        Returns:
            Tuple of three pandas DataFrames (dmdSec, file, structMap).
        """
        self.logger.info("Loading input JSON files...")
        
        # Get file paths from config
        dmdsec_path = Path(self.config["input"]["dmdsec_path"])
        file_path = Path(self.config["input"]["file_path"])
        structmap_path = Path(self.config["input"]["structmap_path"])
        
        # Load JSON files
        dmdsec_df = self._load_and_validate_json(dmdsec_path, "dmdSec")
        file_df = self._load_and_validate_json(file_path, "file")
        structmap_df = self._load_and_validate_json(structmap_path, "structMap")
        
        self.logger.info("Successfully loaded all input JSON files.")
        return dmdsec_df, file_df, structmap_df

    def _load_and_validate_json(self, file_path: Path, table_name: str) -> pd.DataFrame:
        """
        Load a JSON file and validate its structure.

        Args:
            file_path: Path to the JSON file.
            table_name: Name of the table (for logging and validation).

        Returns:
            pandas DataFrame containing the data.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file structure is invalid.
        """
        self.logger.debug(f"Loading {table_name} from {file_path}")
        
        if not file_path.exists():
            error_msg = f"File not found: {file_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Basic validation
            self._validate_dataframe(df, table_name)
            
            return df
        
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in {file_path}: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        except Exception as e:
            error_msg = f"Error loading {table_name}: {str(e)}"
            self.logger.error(error_msg)
            raise

    def _validate_dataframe(self, df: pd.DataFrame, table_name: str) -> None:
        """
        Validate the structure of a DataFrame.

        Args:
            df: DataFrame to validate.
            table_name: Name of the table (for validation rules).

        Raises:
            ValueError: If the DataFrame structure is invalid.
        """
        # Check if DataFrame is empty
        if df.empty:
            error_msg = f"{table_name} data is empty"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Table-specific validations
        if table_name == "dmdSec":
            if "dmd_id" not in df.columns:
                error_msg = f"{table_name} missing required column: dmd_id"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
        
        elif table_name == "file":
            required_columns = ["file_id", "dmd_id"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                error_msg = f"{table_name} missing required columns: {', '.join(missing_columns)}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
        
        elif table_name == "structMap":
            required_columns = ["struct_id", "dmd_id", "parent_id"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                error_msg = f"{table_name} missing required columns: {', '.join(missing_columns)}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
        
        self.logger.debug(f"Validated {table_name} structure: {len(df)} rows, {len(df.columns)} columns")