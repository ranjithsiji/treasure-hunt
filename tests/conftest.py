"""
Conftest file for pytest configuration.
This ensures proper test isolation and database handling.
"""
import pytest
import sys
import os

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
