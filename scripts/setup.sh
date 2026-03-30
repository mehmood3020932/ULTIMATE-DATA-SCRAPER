#!/bin/bash
# Setup script for AI Scraping SaaS

set -e

echo "🚀 Setting up AI Scraping SaaS..."

# Check dependencies
command -v docker >/dev/null 2>&1 || { echo "Docker required"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "Kubectl required"; exit 1; }

# Create namespace
kubectl create namespace ai-scraping --dry-run=client -o yaml | kubectl apply -f -

# Apply configurations
echo "📦 Applying configurations..."
kubectl apply -f infrastructure/kubernetes/configmaps/
kubectl apply -f infrastructure/kubernetes/secrets/

# Deploy infrastructure
echo "🗄️ Deploying infrastructure..."
kubectl apply -f infrastructure/kubernetes/namespaces/

# Deploy services
echo "🚀 Deploying services..."
kubectl apply -f infrastructure/kubernetes/deployments/
kubectl apply -f infrastructure/kubernetes/services/
kubectl apply -f infrastructure/kubernetes/ingress/
kubectl apply -f infrastructure/kubernetes/hpa/

# Run migrations
echo "🔄 Running database migrations..."
kubectl apply -f infrastructure/kubernetes/jobs/db-migration.yaml

echo "✅ Setup complete!"
echo "📊 Check status: kubectl get pods -n ai-scraping"