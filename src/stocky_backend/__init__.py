"""
Stocky Backend - A home kitchen inventory management system

This package provides a FastAPI-based backend for managing inventory,
users, locations, and scanner interactions.
"""

import importlib.metadata

try:
    __version__ = importlib.metadata.version("stocky-backend")
except importlib.metadata.PackageNotFoundError:
    # Fallback version if package not installed
    __version__ = "0.2.1"