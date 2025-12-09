.PHONY: help install proto start test docker clean

help:
	@echo "Bifrost ML Microservice"
	@echo ""
	@echo "Available commands:"
	@echo "  make install  - Install dependencies"
	@echo "  make proto    - Generate gRPC code"
	@echo "  make start    - Start service"
	@echo "  make test     - Run tests"
	@echo "  make docker   - Build Docker image"
	@echo "  make up       - Start with docker-compose"
	@echo "  make down     - Stop docker-compose"
	@echo "  make clean    - Clean generated files"

install:
	pip install -r requirements.txt

proto:
	python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/ml_service.proto

start: proto
	python app.py

test:
	python test_service.py

docker:
	docker build -t bifrost-ml:latest .

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -f proto/*_pb2.py proto/*_pb2_grpc.py 2>/dev/null || true
