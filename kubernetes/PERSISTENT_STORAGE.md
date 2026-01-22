# Persistent Storage (PVC) in Rancher for minyApp

This guide shows how to configure persistent storage for the PostgreSQL database used by **minyApp** when running on a Rancher-managed Kubernetes cluster.

The repository already contains:

- A PersistentVolumeClaim manifest: [kubernetes/pvc.yaml](pvc.yaml)
- A PostgreSQL deployment that mounts this claim: [kubernetes/postgres-deployment.yaml](postgres-deployment.yaml)

---

## 1. How it works

PostgreSQL stores its data under `/var/lib/postgresql/data` inside the container. To make this data survive pod restarts, upgrades, or node failures, we:

1. Create a `PersistentVolumeClaim` (PVC) that requests storage from the cluster.
2. Mount the PVC into the PostgreSQL pod at `/var/lib/postgresql/data`.

Kubernetes then binds this PVC to a `PersistentVolume` (PV) provided by your Rancher cluster's storage backend (for example Longhorn, local-path, NFS, cloud disk, etc.).

---

## 2. Inspect the existing PVC manifest

The file [kubernetes/pvc.yaml](pvc.yaml) looks like this:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: default
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

Key fields:

- `metadata.name`: the PVC name (`postgres-pvc`). This is referenced by the PostgreSQL deployment.
- `namespace`: where the PVC is created. It must match the namespace of your workload.
- `accessModes`: usually `ReadWriteOnce` for a single-node-writable database volume.
- `resources.requests.storage`: requested size of the volume (e.g. `10Gi`).

If your Rancher cluster has a default `StorageClass`, you don't need to specify it here. If you want a specific storage class, add:

```yaml
  storageClassName: my-storage-class
```

under `spec:`.

---

## 3. How the PVC is used by PostgreSQL

The PostgreSQL deployment at [kubernetes/postgres-deployment.yaml](postgres-deployment.yaml) mounts this claim:

```yaml
spec:
  template:
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
          subPath: postgres
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
```

Important parts:

- `volumes[].persistentVolumeClaim.claimName`: refers to `postgres-pvc` from `pvc.yaml`.
- `volumeMounts[].mountPath`: `/var/lib/postgresql/data` is where PostgreSQL writes its data.
- `subPath: postgres`: stores the data inside a `postgres` subdirectory on the underlying volume.

As long as the PVC exists and remains bound, Postgres data will persist even when pods are recreated.

---

## 4. Preparing your Rancher cluster

Before applying these manifests, ensure your Rancher cluster has at least one `StorageClass` that can provision volumes:

1. In the Rancher UI, open your target cluster.
2. Go to **Storage → StorageClasses**.
3. Verify there is a default `StorageClass` (marked with `(default)`), or note the name of the class you want to use.
4. If needed, set one class as default, or update [kubernetes/pvc.yaml](pvc.yaml) to include `storageClassName` with the chosen class name.

If you connect with `kubectl`, you can also list storage classes:

```bash
kubectl get storageclass
```

---

## 5. Creating the PVC and Postgres deployment

Assuming your `kubectl` context is pointed at the Rancher cluster, run from the project root:

```bash
kubectl apply -f kubernetes/pvc.yaml
kubectl apply -f kubernetes/postgres-deployment.yaml
kubectl apply -f kubernetes/postgres-service.yaml
```

Check that the PVC is bound and the pod is running:

```bash
kubectl get pvc -n default
kubectl get pods -n default
```

You should see `postgres-pvc` with `STATUS=Bound` and a `mine-postgres` pod in `Running` state.

---

## 6. Using Rancher UI instead of kubectl

If you prefer the Rancher web UI:

1. Open your cluster in Rancher.
2. Go to **Workloads → PersistentVolumeClaims** (or **Storage → PersistentVolumeClaims**, depending on Rancher version).
3. Click **Create** and fill in:
   - Name: `postgres-pvc` (or your own name, but then update `claimName` in the deployment).
   - Namespace: `default`.
   - Storage class and size: match what you want (e.g. `10Gi`).
4. Save the PVC.
5. Go to **Workloads → Deployments** and either:
   - Import the YAML from [kubernetes/postgres-deployment.yaml](postgres-deployment.yaml), or
   - Edit an existing PostgreSQL deployment and add the same `volumes` and `volumeMounts` sections.

Rancher will provision the volume and attach it to the pod, just like when using `kubectl`.

---

## 7. Persisting additional application data (optional)

If you later decide to persist application logs or other data from the app container, you can:

1. Create another PVC (for example `app-logs-pvc`) based on [kubernetes/pvc.yaml](pvc.yaml), changing the `metadata.name` and size as needed.
2. Add a volume and volumeMount to [kubernetes/app-deployment.yaml](app-deployment.yaml), for example:

```yaml
      containers:
      - name: app
        # ... existing fields ...
        volumeMounts:
        - name: app-logs-storage
          mountPath: /app/logs
      volumes:
      - name: app-logs-storage
        persistentVolumeClaim:
          claimName: app-logs-pvc
```

This will ensure anything written to `/app/logs` in the container is stored on persistent storage managed by Rancher.

---

## 8. Linking with your Docker image built by CI

The GitHub Actions workflow in [.github/workflows/docker-image.yml](../.github/workflows/docker-image.yml) pushes your image to GitHub Container Registry as:

- `ghcr.io/OWNER/REPO:latest`

To use that image in Rancher, update the `image:` field in [kubernetes/app-deployment.yaml](app-deployment.yaml) to match, for example:

```yaml
        image: ghcr.io/YOUR_GITHUB_USER/minyApp:latest
```

After updating, redeploy:

```bash
kubectl apply -f kubernetes/app-deployment.yaml
```

Your app will then run in Rancher using the CI-built Docker image, while PostgreSQL data is kept persistent via the PVC described above.
