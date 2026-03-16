#!/usr/bin/env python3
"""Starlex - Secure Note-Taking Application Entry Point"""

import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from src.app import main

if __name__ == "__main__":
    sys.exit(main())