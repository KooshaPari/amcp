#!/bin/bash
# Start Bifrost ML Service

set -e

echo "Starting Bifrost ML Service..."

# Check if proto files are generated
if [ ! -f "proto/ml_service_pb2.py" ]; then
    echo "Generating gRPC code from proto..."
    python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/ml_service.proto
fi

# Start the service
echo "Starting server on :8001 (HTTP) and :50051 (gRPC)"
python app.py
