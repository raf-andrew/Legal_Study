"""Unit tests for mock queue service."""
import pytest
import yaml
import time
from typing import Dict, Any, List
from ..mocks.services.queue import MockQueueService, MockQueue

@pytest.fixture
def config() -> Dict[str, Any]:
    """Load test configuration."""
    with open(".config/mock.yaml") as f:
        config = yaml.safe_load(f)
    return config["queue"]

@pytest.fixture
def queue_service(config) -> MockQueueService:
    """Create mock queue service instance."""
    return MockQueueService("test_queue", config)

@pytest.fixture
def processed_messages() -> List[Dict[str, Any]]:
    """Store processed messages."""
    return []

@pytest.fixture
def message_handler(processed_messages):
    """Create message handler."""
    def handler(message: Dict[str, Any]):
        processed_messages.append(message)
    return handler

def test_service_initialization(queue_service):
    """Test service initialization."""
    assert queue_service.name == "test_queue"
    assert queue_service._queues == {}

def test_service_start(queue_service):
    """Test service start."""
    queue_service.start()
    assert "tasks" in queue_service._queues
    assert "notifications" in queue_service._queues

def test_service_stop(queue_service):
    """Test service stop."""
    queue_service.start()
    assert len(queue_service._queues) > 0
    
    queue_service.stop()
    assert len(queue_service._queues) == 0

def test_service_reset(queue_service):
    """Test service reset."""
    queue_service.start()
    original_queues = set(queue_service._queues.keys())
    
    # Modify state
    queue_service._queues.clear()
    
    # Reset
    queue_service.reset()
    assert set(queue_service._queues.keys()) == original_queues

def test_create_queue(queue_service):
    """Test creating a queue."""
    queue = queue_service.create_queue("test", max_size=100, consumers=2)
    
    assert isinstance(queue, MockQueue)
    assert queue.name == "test"
    assert queue.max_size == 100
    assert queue.consumers == 2

def test_create_duplicate_queue(queue_service):
    """Test creating a duplicate queue."""
    queue_service.create_queue("test")
    
    with pytest.raises(ValueError):
        queue_service.create_queue("test")

def test_get_queue(queue_service):
    """Test getting a queue."""
    created_queue = queue_service.create_queue("test")
    retrieved_queue = queue_service.get_queue("test")
    
    assert retrieved_queue is created_queue

def test_list_queues(queue_service):
    """Test listing queues."""
    queue_service.start()
    queues = queue_service.list_queues()
    
    assert "tasks" in queues
    assert "notifications" in queues

def test_enqueue_dequeue(queue_service):
    """Test enqueueing and dequeueing messages."""
    queue_service.create_queue("test")
    message = {"id": "1", "content": "test"}
    
    assert queue_service.enqueue("test", message) is True
    dequeued = queue_service.dequeue("test")
    
    assert dequeued == message

def test_enqueue_full_queue(queue_service):
    """Test enqueueing to a full queue."""
    queue_service.create_queue("test", max_size=1)
    
    assert queue_service.enqueue("test", {"id": "1"}) is True
    assert queue_service.enqueue("test", {"id": "2"}) is False

def test_dequeue_empty_queue(queue_service):
    """Test dequeueing from an empty queue."""
    queue_service.create_queue("test")
    assert queue_service.dequeue("test") is None

def test_consumer_processing(queue_service, message_handler, processed_messages):
    """Test message consumer processing."""
    queue = queue_service.create_queue("test", consumers=1)
    queue_service.add_consumer("test", message_handler)
    queue.start()
    
    messages = [
        {"id": "1", "content": "test1"},
        {"id": "2", "content": "test2"}
    ]
    
    for message in messages:
        queue_service.enqueue("test", message)
    
    time.sleep(0.5)  # Wait for processing
    assert len(processed_messages) == 2
    assert processed_messages[0]["id"] in ["1", "2"]
    assert processed_messages[1]["id"] in ["1", "2"]

def test_queue_stats(queue_service, message_handler):
    """Test queue statistics."""
    queue_service.create_queue("test", consumers=1)
    queue_service.add_consumer("test", message_handler)
    queue_service._queues["test"].start()
    
    messages = [
        {"id": "1", "content": "test1"},
        {"id": "2", "content": "test2"}
    ]
    
    for message in messages:
        queue_service.enqueue("test", message)
    
    time.sleep(0.5)  # Wait for processing
    stats = queue_service.get_queue_stats("test")
    
    assert stats["enqueued"] == 2
    assert stats["dequeued"] == 2
    assert stats["processed"] == 2
    assert stats["errors"] == 0
    assert stats["size"] == 0
    assert stats["max_size"] == 1000
    assert stats["consumers"] == 1

def test_all_queues_stats(queue_service):
    """Test statistics for all queues."""
    queue_service.start()
    stats = queue_service.get_all_stats()
    
    assert "tasks" in stats
    assert "notifications" in stats
    assert stats["tasks"]["max_size"] == 1000
    assert stats["tasks"]["consumers"] == 2
    assert stats["notifications"]["max_size"] == 500
    assert stats["notifications"]["consumers"] == 1

def test_error_handling(queue_service):
    """Test error handling in consumer."""
    def error_handler(message: Dict[str, Any]):
        raise ValueError("Test error")
    
    queue = queue_service.create_queue("test", consumers=1)
    queue_service.add_consumer("test", error_handler)
    queue.start()
    
    queue_service.enqueue("test", {"id": "1"})
    time.sleep(0.5)  # Wait for processing
    
    stats = queue_service.get_queue_stats("test")
    assert stats["errors"] == 1

def test_metrics_recording(queue_service):
    """Test metrics recording."""
    queue_service.create_queue("test")
    queue_service.enqueue("test", {"id": "1"})
    queue_service.dequeue("test")
    
    metrics = queue_service.get_metrics()
    assert metrics["total_calls"] == 2
    assert metrics["total_errors"] == 0

def test_error_recording(queue_service):
    """Test error recording."""
    with pytest.raises(ValueError):
        queue_service.enqueue("nonexistent", {})
    
    errors = queue_service.get_errors()
    assert len(errors) == 1
    assert errors[0]["error"] == "Queue not found: nonexistent"

def test_call_recording(queue_service):
    """Test call recording."""
    queue_service.create_queue("test")
    queue_service.enqueue("test", {"id": "1"})
    queue_service.dequeue("test")
    
    calls = queue_service.get_calls()
    assert len(calls) == 2
    assert calls[0]["method"] == "enqueue"
    assert calls[1]["method"] == "dequeue" 