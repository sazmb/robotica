"""
pytest configuration file.

This file ensures the project root is on sys.path so that
`import core`, `import algorithms`, etc. work correctly
when running tests from any directory.

Usage:
    pytest                   # Run all tests
    pytest tests/ -v         # Verbose output
    pytest tests/ --cov=.    # With coverage report
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
