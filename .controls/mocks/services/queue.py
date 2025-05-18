"""Mock queue service implementation."""
import logging
import threading
import queue
import time
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime
from ..base import BaseMockService

logger = logging.getLogger(__name__)

class MockQueue:
    """Mock message queue."""
    
    def __init__(self, name: str, max_size: int = 1000, consumers: int = 1):
        self.name = name
        self.max_size = max_size
        self.consumers = consumers
        self.queue = queue.Queue(maxsize=max_size)
        self.consumer_threads: List[threading.Thread] = []
        self.consumer_handlers: List[Callable[[Dict[str, Any]], None]] = []
        self.running = False
        self.stats = {
            "enqueued": 0,
            "dequeued": 0,
            "errors": 0,
            "processed": 0
        }
        self._lock = threading.Lock()

    def start(self):
        """Start queue consumers."""
        self.running = True
        for i in range(self.consumers):
            thread = threading.Thread(
                target=self._consumer_loop,
                name=f"{self.name}_consumer_{i}",
                daemon=True
            )
            thread.start()
            self.consumer_threads.append(thread)

    def stop(self):
        """Stop queue consumers."""
        self.running = False
        for thread in self.consumer_threads:
            thread.join(timeout=1.0)
        self.consumer_threads.clear()
        self.queue = queue.Queue(maxsize=self.max_size)

    def enqueue(self, message: Dict[str, Any]) -> bool:
        """Enqueue a message."""
        try:
            self.queue.put(message, block=False)
            with self._lock:
                self.stats["enqueued"] += 1
            return True
        except queue.Full:
            return False

    def dequeue(self) -> Optional[Dict[str, Any]]:
        """Dequeue a message."""
        try:
            message = self.queue.get(block=False)
            with self._lock:
                self.stats["dequeued"] += 1
            return message
        except queue.Empty:
            return None

    def add_consumer(self, handler: Callable[[Dict[str, Any]], None]):
        """Add a message consumer."""
        self.consumer_handlers.append(handler)

    def _consumer_loop(self):
        """Consumer thread loop."""
        while self.running:
            try:
                message = self.dequeue()
                if message:
                    for handler in self.consumer_handlers:
                        try:
                            handler(message)
                            with self._lock:
                                self.stats["processed"] += 1
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            with self._lock:
                                self.stats["errors"] += 1
                else:
                    time.sleep(0.1)  # Prevent busy waiting
            except Exception as e:
                logger.error(f"Consumer error: {e}")
                with self._lock:
                    self.stats["errors"] += 1

    def get_stats(self) -> Dict[str, int]:
        """Get queue statistics."""
        with self._lock:
            return {
                "size": self.queue.qsize(),
                "max_size": self.max_size,
                "consumers": self.consumers,
                "enqueued": self.stats["enqueued"],
                "dequeued": self.stats["dequeued"],
                "processed": self.stats["processed"],
                "errors": self.stats["errors"]
            }

class MockQueueService(BaseMockService):
    """Mock queue service."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self._queues: Dict[str, MockQueue] = {}

    def _start(self):
        """Start the mock queue service."""
        self._load_queues()
        for queue in self._queues.values():
            queue.start()

    def _stop(self):
        """Stop the mock queue service."""
        for queue in self._queues.values():
            queue.stop()
        self._queues.clear()

    def _reset(self):
        """Reset the mock queue service."""
        super()._reset()
        self._stop()
        self._load_queues()
        for queue in self._queues.values():
            queue.start()

    def _load_queues(self):
        """Load queues from configuration."""
        queues = self.state.config.get("queues", [])
        for queue_config in queues:
            self.create_queue(
                queue_config["name"],
                queue_config.get("max_size", 1000),
                queue_config.get("consumers", 1)
            )

    def create_queue(self, name: str, max_size: int = 1000, consumers: int = 1) -> MockQueue:
        """Create a queue."""
        if name in self._queues:
            raise ValueError(f"Queue already exists: {name}")
        
        queue = MockQueue(name, max_size, consumers)
        self._queues[name] = queue
        self.logger.info(f"Created queue: {name}")
        return queue

    def get_queue(self, name: str) -> Optional[MockQueue]:
        """Get a queue."""
        return self._queues.get(name)

    def list_queues(self) -> List[str]:
        """List queues."""
        return list(self._queues.keys())

    def enqueue(self, queue: str, message: Dict[str, Any]) -> bool:
        """Enqueue a message."""
        try:
            queue_obj = self.get_queue(queue)
            if not queue_obj:
                raise ValueError(f"Queue not found: {queue}")
            
            self.state.record_call("enqueue", (queue,), {"message": message})
            return queue_obj.enqueue(message)
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "enqueue",
                "queue": queue,
                "message": message
            })
            raise

    def dequeue(self, queue: str) -> Optional[Dict[str, Any]]:
        """Dequeue a message."""
        try:
            queue_obj = self.get_queue(queue)
            if not queue_obj:
                raise ValueError(f"Queue not found: {queue}")
            
            self.state.record_call("dequeue", (queue,), {})
            return queue_obj.dequeue()
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "dequeue",
                "queue": queue
            })
            raise

    def add_consumer(self, queue: str, handler: Callable[[Dict[str, Any]], None]):
        """Add a message consumer."""
        try:
            queue_obj = self.get_queue(queue)
            if not queue_obj:
                raise ValueError(f"Queue not found: {queue}")
            
            self.state.record_call("add_consumer", (queue,), {"handler": handler})
            queue_obj.add_consumer(handler)
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "add_consumer",
                "queue": queue
            })
            raise

    def get_queue_stats(self, queue: str) -> Dict[str, int]:
        """Get queue statistics."""
        try:
            queue_obj = self.get_queue(queue)
            if not queue_obj:
                raise ValueError(f"Queue not found: {queue}")
            
            self.state.record_call("get_queue_stats", (queue,), {})
            return queue_obj.get_stats()
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "get_queue_stats",
                "queue": queue
            })
            raise

    def get_all_stats(self) -> Dict[str, Dict[str, int]]:
        """Get statistics for all queues."""
        try:
            self.state.record_call("get_all_stats", (), {})
            return {
                name: queue.get_stats()
                for name, queue in self._queues.items()
            }
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "get_all_stats"
            })
            raise 