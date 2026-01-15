#!/bin/bash
# Remove from Kubernetes

echo "Removing Mine Gambling Game from Kubernetes..."

kubectl delete hpa mine-app-hpa
kubectl delete svc mine-app mine-postgres
kubectl delete deployment mine-app mine-postgres
kubectl delete pvc postgres-pvc
kubectl delete secret mine-app-secret
kubectl delete configmap mine-app-config

echo "Cleanup complete!"
