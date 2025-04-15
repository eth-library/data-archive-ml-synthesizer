"""
Module for reassembling synthetic data into METS XML.

This module provides functionality to convert synthetic JSON data back into
a valid METS XML document using lxml. It implements the XML structure with
correct tags and namespaces, including dmdSec, amdSec, fileSec, and structMap
sections.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
from lxml import etree


class XMLReassembler:
    """
    Class for reassembling synthetic data into METS XML.
    """

    # METS XML namespaces
    NAMESPACES = {
        'mets': 'http://www.loc.gov/METS/',
        'xlink': 'http://www.w3.org/1999/xlink',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'dnx': 'http://www.exlibrisgroup.com/dps/dnx'
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the XMLReassembler with configuration.

        Args:
            config: Dictionary containing configuration parameters.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    def reassemble(self, synthetic_data: Dict[str, pd.DataFrame], output_path: Optional[str] = None) -> etree._Element:
        """
        Reassemble synthetic data into a METS XML document.

        Args:
            synthetic_data: Dictionary mapping table names to DataFrames containing synthetic data.
            output_path: Optional path to save the XML document. If not provided, uses the path from config.

        Returns:
            lxml Element representing the METS XML document.
        """
        self.logger.info("Reassembling synthetic data into METS XML...")

        # Extract DataFrames
        dmdsec_df = synthetic_data.get('dmdSec')
        file_df = synthetic_data.get('file')
        structmap_df = synthetic_data.get('structMap')

        if dmdsec_df is None or file_df is None or structmap_df is None:
            error_msg = "Missing required synthetic data tables."
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # Create root METS element
        root = self._create_mets_root()

        # Create dmdSec elements
        self._create_dmdsec_elements(root, dmdsec_df)

        # Create amdSec elements
        self._create_amdsec_elements(root)

        # Create fileSec elements
        self._create_filesec_elements(root, file_df)

        # Build file ID mapping
        file_id_mapping = self._build_file_id_mapping(file_df)

        # Create structMap elements with file ID mapping
        self._create_structmap_elements(root, structmap_df, file_id_mapping)

        # Save XML to file if output_path is provided
        if output_path is None and 'xml_output_path' in self.config.get('output', {}):
            output_path = self.config['output']['xml_output_path']

        if output_path:
            self._save_xml(root, output_path)

        self.logger.info("METS XML reassembly completed successfully.")
        return root

    def _create_mets_root(self) -> etree._Element:
        """
        Create the root METS element with appropriate namespaces.

        Returns:
            lxml Element representing the METS root.
        """
        # Register namespaces
        for prefix, uri in self.NAMESPACES.items():
            etree.register_namespace(prefix, uri)

        # Create root element
        mets = etree.Element(f"{{{self.NAMESPACES['mets']}}}mets", nsmap=self.NAMESPACES)

        # Add METS header
        metsHdr = etree.SubElement(mets, f"{{{self.NAMESPACES['mets']}}}metsHdr")
        agent = etree.SubElement(metsHdr, f"{{{self.NAMESPACES['mets']}}}agent", ROLE="CREATOR", TYPE="OTHER")
        name = etree.SubElement(agent, f"{{{self.NAMESPACES['mets']}}}name")
        name.text = "SDV Synthetic Data Generator"

        return mets

    def _create_dmdsec_elements(self, root: etree._Element, dmdsec_df: pd.DataFrame) -> None:
        """
        Create dmdSec elements with Dublin Core records.

        Args:
            root: Root METS element.
            dmdsec_df: DataFrame containing dmdSec data.
        """
        self.logger.debug(f"Creating {len(dmdsec_df)} dmdSec elements")

        for _, row in dmdsec_df.iterrows():
            dmd_id = row['dmd_id']

            # Create dmdSec element
            dmdsec = etree.SubElement(root, f"{{{self.NAMESPACES['mets']}}}dmdSec", ID=dmd_id)

            # Create mdWrap element for Dublin Core
            mdWrap = etree.SubElement(dmdsec, f"{{{self.NAMESPACES['mets']}}}mdWrap", MDTYPE="DC")
            xmlData = etree.SubElement(mdWrap, f"{{{self.NAMESPACES['mets']}}}xmlData")

            # Create Dublin Core record
            dc = etree.SubElement(xmlData, f"{{{self.NAMESPACES['dc']}}}dc")

            # Add Dublin Core elements from row data
            # Exclude dmd_id which is used as ID attribute
            for col, value in row.items():
                if col != 'dmd_id' and pd.notna(value):
                    # Map column names to Dublin Core elements
                    # This is a simplified mapping, adjust as needed
                    if col.startswith('dc_'):
                        element_name = col[3:]  # Remove 'dc_' prefix
                        element = etree.SubElement(dc, f"{{{self.NAMESPACES['dc']}}}{element_name}")
                        element.text = str(value)

    def _create_amdsec_elements(self, root: etree._Element) -> None:
        """
        Create amdSec elements with DNX placeholder content.

        Args:
            root: Root METS element.
        """
        self.logger.debug("Creating amdSec element with DNX placeholder")

        # Create amdSec element
        amdsec = etree.SubElement(root, f"{{{self.NAMESPACES['mets']}}}amdSec")

        # Create techMD element
        techMD = etree.SubElement(amdsec, f"{{{self.NAMESPACES['mets']}}}techMD", ID="AMD1")
        mdWrap = etree.SubElement(techMD, f"{{{self.NAMESPACES['mets']}}}mdWrap", MDTYPE="OTHER", OTHERMDTYPE="DNX")
        xmlData = etree.SubElement(mdWrap, f"{{{self.NAMESPACES['mets']}}}xmlData")

        # Create DNX placeholder content
        dnx = etree.SubElement(xmlData, f"{{{self.NAMESPACES['dnx']}}}dnx")
        section = etree.SubElement(dnx, f"{{{self.NAMESPACES['dnx']}}}section", id="generalRepCharacteristics")
        record = etree.SubElement(section, f"{{{self.NAMESPACES['dnx']}}}record")
        key = etree.SubElement(record, f"{{{self.NAMESPACES['dnx']}}}key", id="preservationType")
        key.text = "PRESERVATION_MASTER"

    def _create_filesec_elements(self, root: etree._Element, file_df: pd.DataFrame) -> None:
        """
        Create fileSec elements with file elements and FLocat elements.

        Args:
            root: Root METS element.
            file_df: DataFrame containing file data.
        """
        self.logger.debug(f"Creating fileSec with {len(file_df)} file elements")

        # Create fileSec element
        filesec = etree.SubElement(root, f"{{{self.NAMESPACES['mets']}}}fileSec")
        fileGrp = etree.SubElement(filesec, f"{{{self.NAMESPACES['mets']}}}fileGrp", USE="CONTENT")

        for _, row in file_df.iterrows():
            file_id = row['file_id']
            dmd_id = row['dmd_id']

            # Create file element
            file_attrs = {
                'ID': file_id,
                'MIMETYPE': row.get('mimetype', 'application/octet-stream'),
                'DMDID': dmd_id
            }

            # Add optional attributes if present
            if 'size' in row and pd.notna(row['size']):
                file_attrs['SIZE'] = str(row['size'])
            if 'checksum' in row and pd.notna(row['checksum']):
                file_attrs['CHECKSUM'] = str(row['checksum'])
                file_attrs['CHECKSUMTYPE'] = row.get('checksumtype', 'MD5')

            file_elem = etree.SubElement(fileGrp, f"{{{self.NAMESPACES['mets']}}}file", **file_attrs)

            # Create FLocat element with XLink attributes
            flocat_attrs = {
                f"{{{self.NAMESPACES['xlink']}}}href": row.get('href', f"file://{file_id}"),
                'LOCTYPE': row.get('loctype', 'URL')
            }
            etree.SubElement(file_elem, f"{{{self.NAMESPACES['mets']}}}FLocat", **flocat_attrs)

    def _build_file_id_mapping(self, file_df: pd.DataFrame) -> Dict[str, str]:
        """
        Build a mapping from original file IDs to synthetic file IDs.

        Args:
            file_df: DataFrame containing file data.

        Returns:
            Dictionary mapping original file IDs to synthetic file IDs.
        """
        file_id_mapping = {}

        # Extract file IDs from the file DataFrame
        for _, row in file_df.iterrows():
            file_id = row['file_id']
            # Store the mapping from original file ID to synthetic file ID
            # The key is the original file ID (e.g., "FILE1") and the value is the synthetic file ID
            # For now, we're just using the file_id as is, but this could be extended to handle
            # more complex mappings if needed
            file_id_mapping[file_id] = file_id

            # If the file_id looks like a synthetic ID (e.g., "sdv-id-XXXXX"),
            # try to extract a potential original ID from it
            if isinstance(file_id, str) and file_id.startswith("sdv-id-"):
                # This is a heuristic approach - we're assuming that the original file IDs
                # might be in the format "FILEX" and we're trying to map them to the synthetic IDs
                for i in range(1, 100):  # Assuming we have at most 99 files
                    original_id = f"FILE{i}"
                    file_id_mapping[original_id] = file_id

        return file_id_mapping

    def _create_structmap_elements(self, root: etree._Element, structmap_df: pd.DataFrame, file_id_mapping: Dict[str, str]) -> None:
        """
        Create structMap elements with nested division hierarchy.

        Args:
            root: Root METS element.
            structmap_df: DataFrame containing structMap data.
            file_id_mapping: Dictionary mapping original file IDs to synthetic file IDs.
        """
        self.logger.debug(f"Creating structMap with {len(structmap_df)} division elements")

        # Create structMap element
        structmap = etree.SubElement(root, f"{{{self.NAMESPACES['mets']}}}structMap", TYPE="LOGICAL")

        # Create a dictionary to store divisions by struct_id for easy lookup
        divisions = {}

        # First pass: create all divisions
        for _, row in structmap_df.iterrows():
            struct_id = row['struct_id']
            dmd_id = row['dmd_id']

            # Create division element
            div_attrs = {
                'ID': struct_id,
                'DMDID': dmd_id
            }

            # Add optional attributes if present
            if 'label' in row and pd.notna(row['label']):
                div_attrs['LABEL'] = str(row['label'])
            if 'order' in row and pd.notna(row['order']):
                div_attrs['ORDER'] = str(row['order'])
            if 'type' in row and pd.notna(row['type']):
                div_attrs['TYPE'] = str(row['type'])

            div = etree.Element(f"{{{self.NAMESPACES['mets']}}}div", **div_attrs)
            divisions[struct_id] = div

            # Add file pointers if present
            if 'file_id' in row and pd.notna(row['file_id']):
                original_file_id = str(row['file_id'])
                # Map the original file ID to the synthetic file ID
                synthetic_file_id = file_id_mapping.get(original_file_id, original_file_id)
                self.logger.debug(f"Mapping file ID: {original_file_id} -> {synthetic_file_id}")
                fptr = etree.SubElement(div, f"{{{self.NAMESPACES['mets']}}}fptr", FILEID=synthetic_file_id)

        # Second pass: build the hierarchy
        root_divs = []
        for _, row in structmap_df.iterrows():
            struct_id = row['struct_id']
            parent_id = row['parent_id']

            if pd.isna(parent_id) or parent_id == '':
                # This is a root division
                root_divs.append(divisions[struct_id])
            else:
                # This is a child division
                if parent_id in divisions:
                    divisions[parent_id].append(divisions[struct_id])

        # Add root divisions to structMap
        for div in root_divs:
            structmap.append(div)

    def _save_xml(self, root: etree._Element, output_path: str) -> None:
        """
        Save the XML document to a file.

        Args:
            root: Root METS element.
            output_path: Path where to save the XML document.
        """
        self.logger.debug(f"Saving XML to {output_path}")

        # Create directory if it doesn't exist
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            # Create XML tree
            tree = etree.ElementTree(root)

            # Write to file with XML declaration and pretty printing
            tree.write(output_path, encoding='utf-8', xml_declaration=True, pretty_print=True)

            self.logger.info(f"XML saved to {output_path}")

        except Exception as e:
            error_msg = f"Error saving XML to {output_path}: {str(e)}"
            self.logger.error(error_msg)
            raise
