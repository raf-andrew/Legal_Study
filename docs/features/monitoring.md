# Monitoring Guide

This guide explains the monitoring system in the Legal Study Platform.

## Overview

The platform implements a comprehensive monitoring system with support for:

- Application metrics
- System metrics
- Logging
- Alerting
- Tracing
- Health checks

## Application Metrics

### 1. Prometheus Integration

```python
# app/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
from functools import wraps
import time

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Business metrics
documents_created_total = Counter(
    'documents_created_total',
    'Total number of documents created'
)

active_users = Gauge(
    'active_users',
    'Number of active users'
)

def track_metrics(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()

        try:
            response = f(*args, **kwargs)
            status = response.status_code
        except Exception as e:
            status = 500
            raise e
        finally:
            duration = time.time() - start_time

            http_requests_total.labels(
                method=request.method,
                endpoint=request.endpoint,
                status=status
            ).inc()

            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=request.endpoint
            ).observe(duration)

        return response
    return decorated_function
```

### 2. Usage

```python
# app/routes/api.py
from app.monitoring.metrics import track_metrics, documents_created_total

@api.route('/documents', methods=['POST'])
@track_metrics
def create_document():
    document = Document.create(request.json)
    documents_created_total.inc()
    return jsonify(document.to_dict())
```

## System Metrics

### 1. System Monitor

```python
# app/monitoring/system.py
import psutil
from prometheus_client import Gauge

# System metrics
cpu_usage = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage'
)

memory_usage = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes'
)

disk_usage = Gauge(
    'disk_usage_bytes',
    'Disk usage in bytes'
)

def collect_system_metrics():
    # CPU metrics
    cpu_usage.set(psutil.cpu_percent())

    # Memory metrics
    memory = psutil.virtual_memory()
    memory_usage.set(memory.used)

    # Disk metrics
    disk = psutil.disk_usage('/')
    disk_usage.set(disk.used)
```

### 2. Database Metrics

```python
# app/monitoring/database.py
from prometheus_client import Gauge, Counter
from sqlalchemy import text

# Database metrics
db_connections = Gauge(
    'db_connections',
    'Number of active database connections'
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type']
)

db_errors = Counter(
    'db_errors_total',
    'Total number of database errors',
    ['error_type']
)

def track_db_metrics(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()

        try:
            result = f(*args, **kwargs)
            duration = time.time() - start_time

            db_query_duration.labels(
                query_type=f.__name__
            ).observe(duration)

            return result
        except Exception as e:
            db_errors.labels(
                error_type=type(e).__name__
            ).inc()
            raise e
    return decorated_function
```

## Logging

### 1. Log Configuration

```python
# app/monitoring/logging.py
import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        if hasattr(record, 'extra'):
            log_record.update(record.extra)

        return json.dumps(log_record)

def setup_logging(app):
    # Create handlers
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(JSONFormatter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    # Configure app logger
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
```

### 2. Usage

```python
# app/routes/api.py
from flask import current_app

@api.route('/documents/<int:id>', methods=['GET'])
def get_document(id):
    current_app.logger.info(
        'Fetching document',
        extra={
            'document_id': id,
            'user_id': g.user.id
        }
    )

    document = Document.query.get_or_404(id)
    return jsonify(document.to_dict())
```

## Alerting

### 1. Alert Manager

```python
# app/monitoring/alerting.py
from prometheus_client import start_http_server
import requests
from app.config import config

class AlertManager:
    def __init__(self):
        self.alertmanager_url = config['alertmanager']['url']
        self.alert_rules = config['alertmanager']['rules']

    def send_alert(self, alert):
        try:
            response = requests.post(
                f"{self.alertmanager_url}/api/v1/alerts",
                json=[alert]
            )
            response.raise_for_status()
        except Exception as e:
            current_app.logger.error(f"Failed to send alert: {str(e)}")

    def check_alerts(self):
        for rule in self.alert_rules:
            if self._evaluate_rule(rule):
                self.send_alert({
                    'labels': rule['labels'],
                    'annotations': rule['annotations']
                })

    def _evaluate_rule(self, rule):
        # Implement rule evaluation logic
        pass
```

### 2. Alert Rules

```yaml
# config/alertmanager/rules.yml
groups:
  - name: application
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
          description: Error rate is above 10% for the last 5 minutes

      - alert: HighLatency
        expr: http_request_duration_seconds{quantile="0.9"} > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High latency detected
          description: 90th percentile latency is above 1 second
```

## Tracing

### 1. OpenTelemetry Integration

```python
# app/monitoring/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

def setup_tracing(app):
    # Create tracer provider
    tracer_provider = TracerProvider()

    # Create Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=config['jaeger']['host'],
        agent_port=config['jaeger']['port']
    )

    # Add span processor
    tracer_provider.add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )

    # Set tracer provider
    trace.set_tracer_provider(tracer_provider)

    # Instrument Flask
    FlaskInstrumentor().instrument_app(app)
```

### 2. Usage

```python
# app/routes/api.py
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@api.route('/documents', methods=['POST'])
def create_document():
    with tracer.start_as_current_span('create_document') as span:
        span.set_attribute('user_id', g.user.id)

        document = Document.create(request.json)
        return jsonify(document.to_dict())
```

## Health Checks

### 1. Health Check Endpoints

```python
# app/monitoring/health.py
from flask import jsonify
import psutil
from app.models import db

@api.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'version': config['version'],
        'timestamp': datetime.utcnow().isoformat()
    })

@api.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    return jsonify({
        'status': 'healthy',
        'version': config['version'],
        'timestamp': datetime.utcnow().isoformat(),
        'system': {
            'cpu': psutil.cpu_percent(),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent
        },
        'database': {
            'connected': db.engine.pool.checkedin() > 0,
            'connections': db.engine.pool.size()
        },
        'redis': {
            'connected': redis_client.ping()
        }
    })
```

### 2. Health Check Service

```python
# app/monitoring/health_service.py
import requests
from datetime import datetime, timedelta

class HealthCheckService:
    def __init__(self):
        self.endpoints = config['health_check']['endpoints']
        self.interval = config['health_check']['interval']
        self.timeout = config['health_check']['timeout']

    def check_endpoints(self):
        results = []

        for endpoint in self.endpoints:
            try:
                response = requests.get(
                    endpoint,
                    timeout=self.timeout
                )
                results.append({
                    'endpoint': endpoint,
                    'status': response.status_code,
                    'response_time': response.elapsed.total_seconds()
                })
            except Exception as e:
                results.append({
                    'endpoint': endpoint,
                    'status': 'error',
                    'error': str(e)
                })

        return results

    def run_checks(self):
        while True:
            results = self.check_endpoints()
            self._store_results(results)
            time.sleep(self.interval)

    def _store_results(self, results):
        # Store results in database or send to monitoring system
        pass
```

## Monitoring Dashboard

### 1. Grafana Configuration

```yaml
# config/grafana/dashboards/app.json
{
  "dashboard": {
    "id": null,
    "title": "Application Dashboard",
    "tags": ["application"],
    "timezone": "browser",
    "panels": [
      {
        "title": "HTTP Requests",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "{{endpoint}}"
          }
        ]
      }
    ]
  }
}
```

### 2. Dashboard Service

```python
# app/monitoring/dashboard.py
import requests
from app.config import config

class DashboardService:
    def __init__(self):
        self.grafana_url = config['grafana']['url']
        self.api_key = config['grafana']['api_key']

    def create_dashboard(self, dashboard_config):
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        response = requests.post(
            f"{self.grafana_url}/api/dashboards/db",
            json=dashboard_config,
            headers=headers
        )
        response.raise_for_status()

        return response.json()

    def update_dashboard(self, dashboard_id, dashboard_config):
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        response = requests.put(
            f"{self.grafana_url}/api/dashboards/db/{dashboard_id}",
            json=dashboard_config,
            headers=headers
        )
        response.raise_for_status()

        return response.json()
```

## Best Practices

1. **Metrics Collection**:
   - Collect relevant metrics
   - Use appropriate metric types
   - Set meaningful labels
   - Follow naming conventions

2. **Logging**:
   - Use structured logging
   - Include context information
   - Set appropriate log levels
   - Implement log rotation

3. **Alerting**:
   - Define clear alert rules
   - Set appropriate thresholds
   - Include actionable information
   - Avoid alert fatigue

4. **Monitoring**:
   - Monitor key metrics
   - Set up dashboards
   - Implement health checks
   - Track business metrics

## Troubleshooting

1. **Metrics Issues**:
   - Check metric collection
   - Verify metric names
   - Check label consistency
   - Monitor metric cardinality

2. **Logging Issues**:
   - Check log configuration
   - Verify log rotation
   - Check log storage
   - Monitor log volume

3. **Alerting Issues**:
   - Check alert rules
   - Verify alert delivery
   - Check alert thresholds
   - Monitor alert volume

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Logging Best Practices](https://www.loggly.com/ultimate-guide/logging-best-practices/)
