#!/bin/bash
# Start the Six Nations Bookie API server

cd "$(dirname "$0")/sixnations_bookie_assets_v2"
echo "Starting API server at http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
echo ""
uvicorn backend_skeleton.main:app --reload --host 0.0.0.0 --port 8000
