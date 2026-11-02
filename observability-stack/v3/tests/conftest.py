"""Pytest configuration to fix imports."""
import sys
import os

# Add parent directory to path so tests can import core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))