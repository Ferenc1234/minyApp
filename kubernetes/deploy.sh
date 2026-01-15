#!/bin/bash
# Deploy to Kubernetes

echo "Deploying Mine Gambling Game to Kubernetes..."

# Apply configurations
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/secret.yaml
kubectl apply -f kubernetes/pvc.yaml

# Deploy database
kubectl apply -f kubernetes/postgres-deployment.yaml
kubectl apply -f kubernetes/postgres-service.yaml

# Wait for database to be ready
echo "Waiting for database to be ready..."
kubectl wait --for=condition=ready pod -l app=mine-postgres --timeout=300s

# Deploy application
kubectl apply -f kubernetes/app-deployment.yaml
kubectl apply -f kubernetes/app-service.yaml
kubectl apply -f kubernetes/hpa.yaml

echo "Deployment complete!"
echo "Getting service info..."
kubectl get svc mine-app

echo ""
echo "To access the application:"
echo "kubectl port-forward svc/mine-app 8000:80"
echo "Then visit http://localhost:8000"
