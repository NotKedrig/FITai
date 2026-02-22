#!/usr/bin/env python
"""Wrapper script to run Alembic migrations programmatically.
This script fixes the issue where the local 'alembic' directory shadows the installed package."""
import sys
import os
import importlib.util
import site

# Find site-packages directory
site_packages = None
for path in site.getsitepackages():
    alembic_init = os.path.join(path, "alembic", "__init__.py")
    if os.path.exists(alembic_init):
        site_packages = path
        break

if not site_packages:
    print("Error: Could not find alembic in site-packages", file=sys.stderr)
    sys.exit(1)

# Remove /app from sys.path to prevent shadowing
original_path = sys.path[:]
sys.path = [p for p in sys.path if p != "/app"]

# Import alembic.config directly from site-packages
alembic_config_path = os.path.join(site_packages, "alembic", "config.py")
if not os.path.exists(alembic_config_path):
    print(f"Error: alembic/config.py not found at {alembic_config_path}", file=sys.stderr)
    sys.exit(1)

# Load alembic.__init__ first
alembic_init_path = os.path.join(site_packages, "alembic", "__init__.py")
alembic_init_spec = importlib.util.spec_from_file_location("alembic", alembic_init_path)
alembic_module = importlib.util.module_from_spec(alembic_init_spec)
sys.modules["alembic"] = alembic_module
alembic_init_spec.loader.exec_module(alembic_module)

# Now load config
spec = importlib.util.spec_from_file_location("alembic.config", alembic_config_path)
alembic_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alembic_config)
sys.modules["alembic.config"] = alembic_config

# Restore path
sys.path = original_path

# Get main function
main = alembic_config.main

if __name__ == "__main__":
    sys.exit(main())
