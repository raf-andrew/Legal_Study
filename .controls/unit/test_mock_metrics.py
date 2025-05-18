"""Unit tests for mock metrics service."""
import pytest
import yaml
from typing import Dict, Any
from ..mocks.services.metrics import (
    MockMetricsService,
    MetricCollector,
    Counter,
    Gauge,
    Histogram
)

@pytest.fixture
def config() -> Dict[str, Any]:
    """Load test configuration."""
    with open(".config/mock.yaml") as f:
        config = yaml.safe_load(f)
    return config["metrics"]

@pytest.fixture
def metrics_service(config) -> MockMetricsService:
    """Create mock metrics service instance."""
    return MockMetricsService("test_metrics", config)

def test_service_initialization(metrics_service):
    """Test service initialization."""
    assert metrics_service.name == "test_metrics"
    assert metrics_service._collectors == {}

def test_service_start(metrics_service):
    """Test service start."""
    metrics_service.start()
    assert "requests" in metrics_service._collectors
    assert "latency" in metrics_service._collectors

def test_service_stop(metrics_service):
    """Test service stop."""
    metrics_service.start()
    assert len(metrics_service._collectors) > 0
    
    metrics_service.stop()
    assert len(metrics_service._collectors) == 0

def test_service_reset(metrics_service):
    """Test service reset."""
    metrics_service.start()
    counter = metrics_service.get_collector("requests")
    counter.inc()
    
    metrics_service.reset()
    assert counter.get() == 0

def test_create_counter(metrics_service):
    """Test creating a counter."""
    counter = metrics_service.create_counter("test", ["label"])
    
    assert isinstance(counter, Counter)
    assert counter.name == "test"
    assert counter.labels == {"label"}

def test_create_gauge(metrics_service):
    """Test creating a gauge."""
    gauge = metrics_service.create_gauge("test", ["label"])
    
    assert isinstance(gauge, Gauge)
    assert gauge.name == "test"
    assert gauge.labels == {"label"}

def test_create_histogram(metrics_service):
    """Test creating a histogram."""
    buckets = [0.1, 0.5, 1.0]
    histogram = metrics_service.create_histogram("test", ["label"], buckets)
    
    assert isinstance(histogram, Histogram)
    assert histogram.name == "test"
    assert histogram.labels == {"label"}
    assert histogram.buckets == buckets

def test_create_duplicate_collector(metrics_service):
    """Test creating a duplicate collector."""
    metrics_service.create_counter("test", ["label"])
    
    with pytest.raises(ValueError):
        metrics_service.create_counter("test", ["label"])

def test_get_collector(metrics_service):
    """Test getting a collector."""
    created = metrics_service.create_counter("test", ["label"])
    retrieved = metrics_service.get_collector("test")
    
    assert retrieved is created

def test_list_collectors(metrics_service):
    """Test listing collectors."""
    metrics_service.start()
    collectors = metrics_service.list_collectors()
    
    assert "requests" in collectors
    assert "latency" in collectors

def test_counter_operations(metrics_service):
    """Test counter operations."""
    counter = metrics_service.create_counter("test", ["method"])
    labels = {"method": "GET"}
    
    counter.inc(labels=labels)
    assert counter.get(labels=labels) == 1.0
    
    counter.inc(2.5, labels=labels)
    assert counter.get(labels=labels) == 3.5

def test_gauge_operations(metrics_service):
    """Test gauge operations."""
    gauge = metrics_service.create_gauge("test", ["status"])
    labels = {"status": "healthy"}
    
    gauge.set(5.0, labels=labels)
    assert gauge.get(labels=labels) == 5.0
    
    gauge.inc(2.0, labels=labels)
    assert gauge.get(labels=labels) == 7.0
    
    gauge.dec(3.0, labels=labels)
    assert gauge.get(labels=labels) == 4.0

def test_histogram_operations(metrics_service):
    """Test histogram operations."""
    buckets = [1.0, 2.0, 3.0]
    histogram = metrics_service.create_histogram("test", ["path"], buckets)
    labels = {"path": "/api"}
    
    histogram.observe(1.5, labels=labels)
    histogram.observe(2.5, labels=labels)
    
    buckets_data = histogram.get_buckets(labels=labels)
    assert buckets_data[1.0] == 0
    assert buckets_data[2.0] == 1
    assert buckets_data[3.0] == 2
    assert buckets_data[float("inf")] == 2
    
    assert histogram.get_sum(labels=labels) == 4.0
    assert histogram.get_count(labels=labels) == 2

def test_collect_metrics(metrics_service):
    """Test collecting metrics."""
    counter = metrics_service.create_counter("requests", ["method"])
    gauge = metrics_service.create_gauge("memory", ["type"])
    histogram = metrics_service.create_histogram("latency", ["path"], [0.1, 0.5, 1.0])
    
    counter.inc(labels={"method": "GET"})
    gauge.set(100.0, labels={"type": "heap"})
    histogram.observe(0.2, labels={"path": "/api"})
    
    metrics = metrics_service.collect()
    
    assert metrics["requests"]["type"] == "counter"
    assert metrics["requests"]["values"]["GET"] == 1.0
    
    assert metrics["memory"]["type"] == "gauge"
    assert metrics["memory"]["values"]["heap"] == 100.0
    
    assert metrics["latency"]["type"] == "histogram"
    assert metrics["latency"]["values"]["api"]["count"] == 1
    assert metrics["latency"]["values"]["api"]["sum"] == 0.2

def test_reset_collector(metrics_service):
    """Test resetting a collector."""
    counter = metrics_service.create_counter("test", [])
    counter.inc()
    
    assert metrics_service.reset_collector("test") is True
    assert counter.get() == 0.0
    assert metrics_service.reset_collector("nonexistent") is False

def test_reset_all(metrics_service):
    """Test resetting all collectors."""
    counter = metrics_service.create_counter("counter", [])
    gauge = metrics_service.create_gauge("gauge", [])
    
    counter.inc()
    gauge.set(1.0)
    
    metrics_service.reset_all()
    assert counter.get() == 0.0
    assert gauge.get() == 0.0

def test_invalid_labels(metrics_service):
    """Test using invalid labels."""
    counter = metrics_service.create_counter("test", ["label1"])
    
    with pytest.raises(ValueError):
        counter.inc(labels={"label2": "value"})

def test_metrics_recording(metrics_service):
    """Test metrics recording."""
    metrics_service.create_counter("test", [])
    metrics_service.collect()
    
    metrics = metrics_service.get_metrics()
    assert metrics["total_calls"] == 1
    assert metrics["total_errors"] == 0

def test_error_recording(metrics_service):
    """Test error recording."""
    with pytest.raises(ValueError):
        metrics_service.reset_collector("nonexistent")
    
    errors = metrics_service.get_errors()
    assert len(errors) == 1

def test_call_recording(metrics_service):
    """Test call recording."""
    metrics_service.create_counter("test", [])
    metrics_service.collect()
    
    calls = metrics_service.get_calls()
    assert len(calls) == 1
    assert calls[0]["method"] == "collect" 