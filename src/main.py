#!/usr/bin/env python3
<<<<<<< HEAD
"""Starlex - Secure Note-Taking Application Entry Point"""
=======
"""TMapp - Secure Note-Taking Application Entry Point"""
>>>>>>> 07f8357c75001a99bd7ebbb69168f8bb8f818e2d

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