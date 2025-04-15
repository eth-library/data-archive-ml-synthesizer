#!/usr/bin/env python3
"""
Main entry point for the METS XML Synthesis Pipeline.

This script serves as a simple wrapper around the pipeline module.
"""

import sys
from src import main

if __name__ == '__main__':
    sys.exit(main())
