#!/bin/bash

# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Run migrations
cd basiclogin
PYTHONPATH=/opt/render/project/src python manage.py migrate

# Collect static files
PYTHONPATH=/opt/render/project/src python manage.py collectstatic --no-input
