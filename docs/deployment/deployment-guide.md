\# Deployment Guide



\## Prerequisites



\- Kubernetes 1.25+

\- Helm 3.0+

\- kubectl configured

\- Docker



\## Quick Deploy



```bash

\# Clone repository

git clone https://github.com/yourorg/ai-scraping-saas.git

cd ai-scraping-saas



\# Setup environment

cp .env.example .env

\# Edit .env with your credentials



\# Deploy to Kubernetes

make k8s-deploy

