#!/bin/bash

# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Run migrations
cd basiclogin
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input
