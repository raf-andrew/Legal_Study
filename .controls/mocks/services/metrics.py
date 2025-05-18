"""Mock metrics service implementation."""
import logging
import threading
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from datetime import datetime, timedelta
from collections import defaultdict
from ..base import BaseMockService

logger = logging.getLogger(__name__)

class MetricCollector:
    """Base metric collector."""
    
    def __init__(self, name: str, labels: List[str]):
        self.name = name
        self.labels = set(labels)
        self.created_at = datetime.now()
        self._lock = threading.Lock()

    def validate_labels(self, labels: Dict[str, str]):
        """Validate label names."""
        if not self.labels >= set(labels.keys()):
            raise ValueError(f"Invalid labels. Expected: {self.labels}, got: {set(labels.keys())}")

class Counter(MetricCollector):
    """Counter metric collector."""
    
    def __init__(self, name: str, labels: List[str]):
        super().__init__(name, labels)
        self._values: Dict[Tuple[str, ...], float] = defaultdict(float)

    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment counter."""
        labels = labels or {}
        self.validate_labels(labels)
        
        label_values = tuple(labels.get(label, "") for label in sorted(self.labels))
        with self._lock:
            self._values[label_values] += amount

    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get counter value."""
        labels = labels or {}
        self.validate_labels(labels)
        
        label_values = tuple(labels.get(label, "") for label in sorted(self.labels))
        with self._lock:
            return self._values[label_values]

    def reset(self):
        """Reset counter."""
        with self._lock:
            self._values.clear()

class Gauge(MetricCollector):
    """Gauge metric collector."""
    
    def __init__(self, name: str, labels: List[str]):
        super().__init__(name, labels)
        self._values: Dict[Tuple[str, ...], float] = defaultdict(float)

    def set(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Set gauge value."""
        labels = labels or {}
        self.validate_labels(labels)
        
        label_values = tuple(labels.get(label, "") for label in sorted(self.labels))
        with self._lock:
            self._values[label_values] = value

    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment gauge."""
        labels = labels or {}
        self.validate_labels(labels)
        
        label_values = tuple(labels.get(label, "") for label in sorted(self.labels))
        with self._lock:
            self._values[label_values] += amount

    def dec(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Decrement gauge."""
        labels = labels or {}
        self.validate_labels(labels)
        
        label_values = tuple(labels.get(label, "") for label in sorted(self.labels))
        with self._lock:
            self._values[label_values] -= amount

    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get gauge value."""
        labels = labels or {}
        self.validate_labels(labels)
        
        label_values = tuple(labels.get(label, "") for label in sorted(self.labels))
        with self._lock:
            return self._values[label_values]

    def reset(self):
        """Reset gauge."""
        with self._lock:
            self._values.clear()

class Histogram(MetricCollector):
    """Histogram metric collector."""
    
    def __init__(self, name: str, labels: List[str], buckets: List[float]):
        super().__init__(name, labels)
        self.buckets = sorted(buckets)
        self._values: Dict[Tuple[str, ...], List[float]] = defaultdict(list)
        self._counts: Dict[Tuple[str, ...], Dict[float, int]] = defaultdict(
            lambda: {float("inf"): 0, **{b: 0 for b in self.buckets}}
        )

    def observe(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Record observation."""
        labels = labels or {}
        self.validate_labels(labels)
        
        label_values = tuple(labels.get(label, "") for label in sorted(self.labels))
        with self._lock:
            self._values[label_values].append(value)
            for bucket in self._counts[label_values]:
                if value <= bucket:
                    self._counts[label_values][bucket] += 1

    def get_buckets(self, labels: Optional[Dict[str, str]] = None) -> Dict[float, int]:
        """Get histogram buckets."""
        labels = labels or {}
        self.validate_labels(labels)
        
        label_values = tuple(labels.get(label, "") for label in sorted(self.labels))
        with self._lock:
            return dict(self._counts[label_values])

    def get_sum(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get sum of observations."""
        labels = labels or {}
        self.validate_labels(labels)
        
        label_values = tuple(labels.get(label, "") for label in sorted(self.labels))
        with self._lock:
            return sum(self._values[label_values])

    def get_count(self, labels: Optional[Dict[str, str]] = None) -> int:
        """Get count of observations."""
        labels = labels or {}
        self.validate_labels(labels)
        
        label_values = tuple(labels.get(label, "") for label in sorted(self.labels))
        with self._lock:
            return len(self._values[label_values])

    def reset(self):
        """Reset histogram."""
        with self._lock:
            self._values.clear()
            self._counts.clear()

class MockMetricsService(BaseMockService):
    """Mock metrics service."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self._collectors: Dict[str, MetricCollector] = {}

    def _start(self):
        """Start the mock metrics service."""
        self._load_collectors()

    def _stop(self):
        """Stop the mock metrics service."""
        self._collectors.clear()

    def _reset(self):
        """Reset the mock metrics service."""
        super()._reset()
        for collector in self._collectors.values():
            collector.reset()

    def _load_collectors(self):
        """Load collectors from configuration."""
        collectors = self.state.config.get("collectors", [])
        for collector_config in collectors:
            name = collector_config["name"]
            type_ = collector_config["type"]
            labels = collector_config.get("labels", [])
            
            if type_ == "counter":
                self.create_counter(name, labels)
            elif type_ == "gauge":
                self.create_gauge(name, labels)
            elif type_ == "histogram":
                buckets = collector_config.get("buckets", [0.1, 0.5, 1.0, 2.0, 5.0])
                self.create_histogram(name, labels, buckets)

    def create_counter(self, name: str, labels: List[str]) -> Counter:
        """Create a counter."""
        if name in self._collectors:
            raise ValueError(f"Collector already exists: {name}")
        
        counter = Counter(name, labels)
        self._collectors[name] = counter
        self.logger.info(f"Created counter: {name}")
        return counter

    def create_gauge(self, name: str, labels: List[str]) -> Gauge:
        """Create a gauge."""
        if name in self._collectors:
            raise ValueError(f"Collector already exists: {name}")
        
        gauge = Gauge(name, labels)
        self._collectors[name] = gauge
        self.logger.info(f"Created gauge: {name}")
        return gauge

    def create_histogram(self, name: str, labels: List[str], buckets: List[float]) -> Histogram:
        """Create a histogram."""
        if name in self._collectors:
            raise ValueError(f"Collector already exists: {name}")
        
        histogram = Histogram(name, labels, buckets)
        self._collectors[name] = histogram
        self.logger.info(f"Created histogram: {name}")
        return histogram

    def get_collector(self, name: str) -> Optional[MetricCollector]:
        """Get a collector."""
        return self._collectors.get(name)

    def list_collectors(self) -> List[str]:
        """List collectors."""
        return list(self._collectors.keys())

    def collect(self) -> Dict[str, Dict[str, Any]]:
        """Collect all metrics."""
        try:
            self.state.record_call("collect", (), {})
            
            metrics = {}
            for name, collector in self._collectors.items():
                if isinstance(collector, Counter):
                    metrics[name] = {
                        "type": "counter",
                        "values": {
                            "_".join(str(v) for v in k) or "total": v
                            for k, v in collector._values.items()
                        }
                    }
                elif isinstance(collector, Gauge):
                    metrics[name] = {
                        "type": "gauge",
                        "values": {
                            "_".join(str(v) for v in k) or "total": v
                            for k, v in collector._values.items()
                        }
                    }
                elif isinstance(collector, Histogram):
                    metrics[name] = {
                        "type": "histogram",
                        "values": {
                            label_key: {
                                "buckets": buckets,
                                "sum": collector.get_sum(dict(zip(collector.labels, label_values))),
                                "count": collector.get_count(dict(zip(collector.labels, label_values)))
                            }
                            for label_values in collector._values.keys()
                            for label_key in ["_".join(str(v) for v in label_values) or "total"]
                            for buckets in [collector.get_buckets(dict(zip(collector.labels, label_values)))]
                        }
                    }
            
            return metrics
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "collect"
            })
            raise

    def reset_collector(self, name: str) -> bool:
        """Reset a collector."""
        try:
            self.state.record_call("reset_collector", (name,), {})
            
            collector = self.get_collector(name)
            if not collector:
                return False
            
            collector.reset()
            return True
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "reset_collector",
                "name": name
            })
            raise

    def reset_all(self):
        """Reset all collectors."""
        try:
            self.state.record_call("reset_all", (), {})
            self._reset()
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "reset_all"
            })
            raise 