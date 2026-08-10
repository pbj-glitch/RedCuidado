#!/bin/bash
# build_files.sh
echo "Installing dependencies..."
pip install -r requirements.txt --break-system-packages
echo "Running collectstatic..."
python3 manage.py collectstatic --noinput --clear
