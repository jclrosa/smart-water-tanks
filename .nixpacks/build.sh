#!/bin/bash
set -e

# Set environment variables for PostgreSQL
export LDFLAGS="-L/nix/store/*/lib"
export CPPFLAGS="-I/nix/store/*/include"

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput 