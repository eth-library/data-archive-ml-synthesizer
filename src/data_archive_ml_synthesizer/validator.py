"""
Module for validating METS XML against XSD schemas.

This module provides functionality to validate the generated METS XML
against XSD schemas using the xmlschema package. It validates the XML
document against the provided XSD schemas for METS, Dublin Core, and DNX.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Union, Tuple

import xmlschema
from lxml import etree


class XMLValidator:
    """
    Class for validating METS XML against XSD schemas.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the XMLValidator with configuration.

        Args:
            config: Dictionary containing configuration parameters including XSD schema paths.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.schemas = {}

    def validate(self, xml_path: Union[str, Path], 
                detailed_output: bool = False) -> Union[bool, Tuple[bool, List[str]]]:
        """
        Validate a METS XML document against XSD schemas.

        Args:
            xml_path: Path to the XML document to validate.
            detailed_output: If True, returns a tuple with validation result and error messages.
                            If False, returns only the validation result.

        Returns:
            If detailed_output is False, returns True if validation succeeds, False otherwise.
            If detailed_output is True, returns a tuple (success, error_messages).
        """
        self.logger.info(f"Validating XML document: {xml_path}")
        
        # Load schemas if not already loaded
        if not self.schemas:
            self._load_schemas()
        
        # Parse XML document
        try:
            xml_doc = etree.parse(str(xml_path))
        except Exception as e:
            error_msg = f"Error parsing XML document: {str(e)}"
            self.logger.error(error_msg)
            return (False, [error_msg]) if detailed_output else False
        
        # Validate against each schema
        all_valid = True
        error_messages = []
        
        for schema_name, schema in self.schemas.items():
            self.logger.debug(f"Validating against {schema_name} schema")
            
            try:
                schema.validate(xml_doc)
                self.logger.debug(f"Validation against {schema_name} schema succeeded")
            
            except xmlschema.XMLSchemaValidationError as e:
                all_valid = False
                error_msg = f"Validation against {schema_name} schema failed: {str(e)}"
                self.logger.error(error_msg)
                error_messages.append(error_msg)
            
            except Exception as e:
                all_valid = False
                error_msg = f"Error during validation against {schema_name} schema: {str(e)}"
                self.logger.error(error_msg)
                error_messages.append(error_msg)
        
        if all_valid:
            self.logger.info("XML document is valid against all schemas")
        else:
            self.logger.error("XML document is invalid against one or more schemas")
        
        return (all_valid, error_messages) if detailed_output else all_valid

    def validate_element(self, xml_element: etree._Element, 
                        detailed_output: bool = False) -> Union[bool, Tuple[bool, List[str]]]:
        """
        Validate an XML element against XSD schemas.

        Args:
            xml_element: lxml Element to validate.
            detailed_output: If True, returns a tuple with validation result and error messages.
                            If False, returns only the validation result.

        Returns:
            If detailed_output is False, returns True if validation succeeds, False otherwise.
            If detailed_output is True, returns a tuple (success, error_messages).
        """
        self.logger.info("Validating XML element")
        
        # Load schemas if not already loaded
        if not self.schemas:
            self._load_schemas()
        
        # Validate against each schema
        all_valid = True
        error_messages = []
        
        for schema_name, schema in self.schemas.items():
            self.logger.debug(f"Validating against {schema_name} schema")
            
            try:
                schema.validate(xml_element)
                self.logger.debug(f"Validation against {schema_name} schema succeeded")
            
            except xmlschema.XMLSchemaValidationError as e:
                all_valid = False
                error_msg = f"Validation against {schema_name} schema failed: {str(e)}"
                self.logger.error(error_msg)
                error_messages.append(error_msg)
            
            except Exception as e:
                all_valid = False
                error_msg = f"Error during validation against {schema_name} schema: {str(e)}"
                self.logger.error(error_msg)
                error_messages.append(error_msg)
        
        if all_valid:
            self.logger.info("XML element is valid against all schemas")
        else:
            self.logger.error("XML element is invalid against one or more schemas")
        
        return (all_valid, error_messages) if detailed_output else all_valid

    def _load_schemas(self) -> None:
        """
        Load XSD schemas from paths specified in configuration.
        """
        self.logger.debug("Loading XSD schemas")
        
        schema_paths = self.config.get('validation', {}).get('schema_paths', {})
        
        if not schema_paths:
            error_msg = "No schema paths specified in configuration"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Load each schema
        for schema_name, schema_path in schema_paths.items():
            self.logger.debug(f"Loading {schema_name} schema from {schema_path}")
            
            try:
                schema = xmlschema.XMLSchema(schema_path)
                self.schemas[schema_name] = schema
                self.logger.debug(f"Loaded {schema_name} schema successfully")
            
            except Exception as e:
                error_msg = f"Error loading {schema_name} schema from {schema_path}: {str(e)}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
        
        self.logger.info(f"Loaded {len(self.schemas)} XSD schemas")