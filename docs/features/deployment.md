# Deployment Guide

This guide explains the deployment system in the Legal Study Platform.

## Overview

The platform uses a containerized deployment strategy with support for:

- Docker containers
- Kubernetes orchestration
- CI/CD pipelines
- Environment management
- Monitoring and logging

## Docker Configuration

### 1. Base Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]
```

### 2. Development Dockerfile

```dockerfile
# Dockerfile.dev
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=app \
    FLASK_ENV=development

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Copy application code
COPY . .

# Run the development server
CMD ["flask", "run", "--host=0.0.0.0"]
```

### 3. Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/legal_study
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - .:/app
    networks:
      - app-network

  db:
    image: postgres:13
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=legal_study
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network

  redis:
    image: redis:6
    volumes:
      - redis_data:/data
    networks:
      - app-network

volumes:
  postgres_data:
  redis_data:

networks:
  app-network:
    driver: bridge
```

## Kubernetes Configuration

### 1. Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: legal-study
  namespace: legal-study
spec:
  replicas: 3
  selector:
    matchLabels:
      app: legal-study
  template:
    metadata:
      labels:
        app: legal-study
    spec:
      containers:
      - name: legal-study
        image: legal-study:latest
        ports:
        - containerPort: 5000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: legal-study-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: legal-study-secrets
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 2. Service

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: legal-study
  namespace: legal-study
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 5000
  selector:
    app: legal-study
```

### 3. Ingress

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: legal-study
  namespace: legal-study
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - legal-study.example.com
    secretName: legal-study-tls
  rules:
  - host: legal-study.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: legal-study
            port:
              number: 80
```

## CI/CD Pipeline

### 1. GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v1

    - name: Login to DockerHub
      uses: docker/login-action@v1
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}

    - name: Build and push
      uses: docker/build-push-action@v2
      with:
        context: .
        push: true
        tags: legal-study:latest

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v2

    - name: Install kubectl
      uses: azure/setup-kubectl@v1

    - name: Set up kubeconfig
      run: |
        echo "${{ secrets.KUBE_CONFIG }}" > kubeconfig.yaml
        export KUBECONFIG=kubeconfig.yaml

    - name: Deploy to Kubernetes
      run: |
        kubectl apply -f k8s/
```

## Environment Configuration

### 1. ConfigMaps

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: legal-study-config
  namespace: legal-study
data:
  LOG_LEVEL: "INFO"
  MAX_CONNECTIONS: "100"
  CACHE_TTL: "300"
  SESSION_TIMEOUT: "3600"
```

### 2. Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: legal-study-secrets
  namespace: legal-study
type: Opaque
data:
  database-url: <base64-encoded-url>
  redis-url: <base64-encoded-url>
  jwt-secret: <base64-encoded-secret>
```

## Monitoring and Logging

### 1. Prometheus Configuration

```yaml
# k8s/prometheus.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: legal-study
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: legal-study
  endpoints:
  - port: metrics
    interval: 15s
```

### 2. Grafana Dashboard

```json
# k8s/grafana-dashboard.json
{
  "dashboard": {
    "id": null,
    "title": "Legal Study Platform",
    "tags": ["legal-study"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{path}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "rate(http_errors_total[5m])",
            "legendFormat": "{{method}} {{path}}"
          }
        ]
      }
    ]
  }
}
```

### 3. Logging Configuration

```yaml
# k8s/fluentd.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: logging
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      read_from_head true
      <parse>
        @type json
        time_format %Y-%m-%dT%H:%M:%S.%NZ
      </parse>
    </source>

    <match kubernetes.**>
      @type elasticsearch
      host elasticsearch
      port 9200
      logstash_format true
      logstash_prefix k8s
      <buffer>
        @type file
        path /var/log/fluentd-buffers/kubernetes.buffer
        flush_mode interval
        timekey 1h
        timekey_use_utc true
        timekey_wait 10m
      </buffer>
    </match>
```

## Backup and Recovery

### 1. Database Backup

```yaml
# k8s/backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-backup
  namespace: legal-study
spec:
  schedule: "0 0 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:13
            command:
            - /bin/sh
            - -c
            - |
              pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > /backup/backup.sql
            env:
            - name: DB_HOST
              valueFrom:
                secretKeyRef:
                  name: legal-study-secrets
                  key: database-host
            - name: DB_USER
              valueFrom:
                secretKeyRef:
                  name: legal-study-secrets
                  key: database-user
            - name: DB_NAME
              valueFrom:
                secretKeyRef:
                  name: legal-study-secrets
                  key: database-name
            volumeMounts:
            - name: backup-volume
              mountPath: /backup
          volumes:
          - name: backup-volume
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
```

### 2. Database Recovery

```yaml
# k8s/restore-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-restore
  namespace: legal-study
spec:
  template:
    spec:
      containers:
      - name: restore
        image: postgres:13
        command:
        - /bin/sh
        - -c
        - |
          psql -h $DB_HOST -U $DB_USER -d $DB_NAME < /backup/backup.sql
        env:
        - name: DB_HOST
          valueFrom:
            secretKeyRef:
              name: legal-study-secrets
              key: database-host
        - name: DB_USER
          valueFrom:
            secretKeyRef:
              name: legal-study-secrets
              key: database-user
        - name: DB_NAME
          valueFrom:
            secretKeyRef:
              name: legal-study-secrets
              key: database-name
        volumeMounts:
        - name: backup-volume
          mountPath: /backup
      volumes:
      - name: backup-volume
        persistentVolumeClaim:
          claimName: backup-pvc
      restartPolicy: OnFailure
```

## Security

### 1. Network Policies

```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: legal-study-network-policy
  namespace: legal-study
spec:
  podSelector:
    matchLabels:
      app: legal-study
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 5000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: database
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - namespaceSelector:
        matchLabels:
          name: redis
    ports:
    - protocol: TCP
      port: 6379
```

### 2. Pod Security Policy

```yaml
# k8s/pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: legal-study-psp
spec:
  privileged: false
  seLinux:
    rule: RunAsAny
  runAsUser:
    rule: MustRunAsNonRoot
    ranges:
    - min: 1000
      max: 65535
  fsGroup:
    rule: MustRunAs
    ranges:
    - min: 1000
      max: 65535
  volumes:
  - 'configMap'
  - 'emptyDir'
  - 'projected'
  - 'secret'
  - 'downwardAPI'
  - 'persistentVolumeClaim'
```

## Best Practices

1. **Container Security**:
   - Use non-root users
   - Scan for vulnerabilities
   - Keep images updated
   - Use minimal base images

2. **Resource Management**:
   - Set resource limits
   - Monitor resource usage
   - Implement autoscaling
   - Use resource quotas

3. **High Availability**:
   - Use multiple replicas
   - Implement health checks
   - Use pod disruption budgets
   - Configure anti-affinity

4. **Monitoring**:
   - Collect metrics
   - Set up alerts
   - Monitor logs
   - Track performance

## Troubleshooting

1. **Deployment Issues**:
   - Check pod status
   - Review logs
   - Verify configurations
   - Check resource limits

2. **Performance Issues**:
   - Monitor metrics
   - Check resource usage
   - Review scaling settings
   - Analyze bottlenecks

3. **Security Issues**:
   - Review access logs
   - Check security policies
   - Verify network rules
   - Audit configurations

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
