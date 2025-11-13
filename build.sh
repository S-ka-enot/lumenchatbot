#!/bin/bash
# Build script for Coolify
# This script builds the application using the Dockerfile

set -e

echo "Building LumenChat backend service..."
docker build -t lumenpay-backend:latest .

echo "Build completed successfully!"
