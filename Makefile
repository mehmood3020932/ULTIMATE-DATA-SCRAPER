# Makefile for AI Scraping SaaS

.PHONY: all build up down test lint clean

# Docker Compose commands
up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build

logs:
	docker-compose logs -f

# Kubernetes commands
k8s-deploy:
	kubectl apply -f infrastructure/kubernetes/namespaces/
	kubectl apply -f infrastructure/kubernetes/configmaps/
	kubectl apply -f infrastructure/kubernetes/secrets/
	kubectl apply -f infrastructure/kubernetes/deployments/
	kubectl apply -f infrastructure/kubernetes/services/
	kubectl apply -f infrastructure/kubernetes/ingress/
	kubectl apply -f infrastructure/kubernetes/hpa/

k8s-delete:
	kubectl delete namespace ai-scraping

# Database migrations
migrate-up:
	cd databases/postgres && psql -d scraping -f migrations/001_initial.sql
	cd databases/postgres && psql -d scraping -f migrations/002_add_jobs.sql
	cd databases/postgres && psql -d scraping -f migrations/003_add_billing.sql
	cd databases/postgres && psql -d scraping -f migrations/004_add_analytics.sql

# Testing
test:
	cd services/api-service && pytest
	cd services/agent-service && pytest

# Linting
lint:
	cd services/api-service && flake8 app/
	cd services/agent-service && flake8 app/
	cd services/worker-service && golangci-lint run
	cd services/realtime-service && npm run lint

# Cleaning
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete