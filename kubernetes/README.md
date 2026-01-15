# Kubernetes Deployment Guide

## Prerequisites

- Kubernetes cluster (1.19+)
- kubectl configured
- Docker image built and accessible

## Deployment Steps

### 1. Build Docker Image

```bash
docker build -t mine-app:latest .
```

If using a Docker registry:
```bash
docker build -t <registry>/mine-app:latest .
docker push <registry>/mine-app:latest
```

Update the image reference in `kubernetes/app-deployment.yaml` if needed.

### 2. Deploy to Kubernetes

Option A: Using the deployment script:
```bash
chmod +x kubernetes/deploy.sh
./kubernetes/deploy.sh
```

Option B: Manual deployment:
```bash
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/secret.yaml
kubectl apply -f kubernetes/pvc.yaml
kubectl apply -f kubernetes/postgres-deployment.yaml
kubectl apply -f kubernetes/postgres-service.yaml
kubectl apply -f kubernetes/app-deployment.yaml
kubectl apply -f kubernetes/app-service.yaml
kubectl apply -f kubernetes/hpa.yaml
```

### 3. Verify Deployment

```bash
# Check pods
kubectl get pods

# Check services
kubectl get svc

# Check deployment status
kubectl get deployment

# View logs
kubectl logs -f deployment/mine-app

# Describe pod (for debugging)
kubectl describe pod <pod-name>
```

### 4. Access the Application

For LoadBalancer service:
```bash
kubectl get svc mine-app
# Note the EXTERNAL-IP and visit http://EXTERNAL-IP
```

For local testing with port-forward:
```bash
kubectl port-forward svc/mine-app 8000:80
# Visit http://localhost:8000
```

## Configuration

### Environment Variables

Edit `kubernetes/secret.yaml` to change:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret key

Edit `kubernetes/configmap.yaml` to change:
- `LOG_LEVEL` - Application log level
- `ACCESS_TOKEN_EXPIRE_MINUTES` - JWT token expiry

### Scaling

Manual scaling:
```bash
kubectl scale deployment mine-app --replicas=5
```

HPA will automatically scale based on CPU/Memory usage:
- Minimum replicas: 2
- Maximum replicas: 10
- Target CPU utilization: 70%
- Target Memory utilization: 80%

## Database

The PostgreSQL database is deployed as a single-replica StatefulSet with persistent storage.

Access the database:
```bash
kubectl exec -it deployment/mine-postgres -- psql -U mineuser -d minedb
```

### Backup

```bash
# Backup database
kubectl exec deployment/mine-postgres -- pg_dump -U mineuser minedb > backup.sql

# Restore database
kubectl exec -i deployment/mine-postgres -- psql -U mineuser minedb < backup.sql
```

## Monitoring

### Check application health

```bash
kubectl get endpoints mine-app
```

### View application metrics

```bash
# If metrics-server is installed
kubectl top pod
kubectl top nodes
```

## Troubleshooting

### Pod won't start

```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Database connection issues

```bash
# Test database connection
kubectl exec -it deployment/mine-app -- python -c "
from app.database import engine
engine.execute('SELECT 1')
print('Database connected!')
"
```

### Storage issues

```bash
kubectl get pvc
kubectl describe pvc postgres-pvc
```

## Cleanup

Option A: Using the undeploy script:
```bash
chmod +x kubernetes/undeploy.sh
./kubernetes/undeploy.sh
```

Option B: Manual cleanup:
```bash
kubectl delete -f kubernetes/
```

## Production Considerations

1. **Secrets Management**: Use a proper secrets manager (Sealed Secrets, Vault, etc.)
2. **Image Registry**: Push images to a private registry
3. **Ingress**: Set up Ingress for better routing and TLS
4. **Network Policies**: Restrict pod-to-pod communication
5. **Resource Quotas**: Set namespace resource limits
6. **RBAC**: Configure role-based access control
7. **Monitoring**: Install Prometheus and Grafana
8. **Logging**: Set up centralized logging (ELK, Loki, etc.)
9. **Backup Strategy**: Regular database backups
10. **Security**: Regular security audits and updates
