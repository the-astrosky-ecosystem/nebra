# tests/utilities.py

import json
import threading
import time
import typing as t
from typing import Any

from atproto_jetstream import SubscribeEventsMessage

from nebra.floats import encode_floats_in_event
from nebra.rebroadcast import DataSource


class DummyDataSource(DataSource):
    """A dummy data source for testing that generates simple events."""

    def __init__(self, max_queue_size: int = 1000, event_delay: float = 0.1):
        """Initialize the dummy data source.

        Args:
            max_queue_size: Maximum size of the event queue.
            event_delay: Delay between events in seconds.
        """
        super().__init__(max_queue_size)
        self.event_delay = event_delay
        self.event_counter = 0

    def run(self) -> None:
        """Run the dummy data source, generating simple test events."""
        while not self.stop_event.is_set():
            # Generate a simple event with a $type and value field
            event = {
                "$type": "com.example.test",
                "value": f"test_value_{self.event_counter}",
                "counter": self.event_counter,
            }
            
            # Add the event to the queue
            self.add_event(event)
            self.event_counter += 1
            
            # Sleep for the specified delay
            time.sleep(self.event_delay)


def dummy_send(event: dict, **kwargs: Any) -> None:
    """A dummy send function that validates an event would be valid for ATProto.
    
    This function mirrors the behavior of the send function in client.py,
    but instead of posting to ATProto, it validates that the event would be
    valid for client.com.atproto.repo.create_record.
    
    Args:
        event: The event to validate.
        **kwargs: Additional arguments (ignored for validation).
        
    Raises:
        ValueError: If the event is not valid for ATProto.
    """
    # Check that the event has a $type field
    if "$type" not in event:
        raise ValueError("Event must have a $type field")
    
    # Check that the $type field is a non-empty string
    if not isinstance(event["$type"], str) or not event["$type"].strip():
        raise ValueError("$type field must be a non-empty string")
    
    # Check that the event is a dictionary (record must be a dict)
    if not isinstance(event, dict):
        raise TypeError("Event must be a dictionary")
    
    # If we got here, the event is valid
    print(f"Event validated successfully: {event}")


class DummyJetstreamClient:
    """A dummy Jetstream client for testing that generates mock events."""

    def __init__(
        self,
        params: dict | None = None,
        base_uri: str = "wss://dummy.jetstream",
        compress: bool = False,
        event_delay: float = 0.1,
        event_count: int = 5,
    ):
        """Initialize the dummy client.
        
        Args:
            params: Subscription parameters (ignored in dummy client)
            base_uri: Base URI (ignored in dummy client)
            compress: Whether to use compression (ignored in dummy client)
            event_delay: Delay between events in seconds
            event_count: Number of events to generate
        """
        self.params = params or {}
        self.base_uri = base_uri
        self.compress = compress
        self.event_delay = event_delay
        self.event_count = event_count
        self.stop_event = threading.Event()
        self.thread = None
        self.message_handler = None

    def start(self, message_handler: t.Callable[[SubscribeEventsMessage], None]) -> None:
        """Start generating mock events."""
        self.message_handler = message_handler
        self.thread = threading.Thread(target=self._generate_events)
        self.thread.start()

    def stop(self) -> None:
        """Stop generating mock events."""
        self.stop_event.set()
        if self.thread:
            self.thread.join()

    def _generate_events(self) -> None:
        """Generate mock events."""
        for i in range(self.event_count):
            if self.stop_event.is_set():
                break
                
            # Create a mock event with various data types
            event = {
                "$type": "com.example.test",
                "seq": i,
                "operation": "create",
                "record": {
                    "text": f"Test event {i}",
                    "float_value": 3.14159 + i,
                    "int_value": i,
                    "bool_value": i % 2 == 0,
                    "nested": {
                        "float_list": [1.0 + i, 2.5 + i, 3.7 + i],
                        "mixed_data": ["text", 42, 4.2 + i, True, None]
                    }
                }
            }
            
            # Encode floats in the event
            encoded_event = encode_floats_in_event(event)
            
            # Create a mock message object with the required attributes
            message = type('SubscribeEventsMessage', (), {
                'op': event.get("operation", "create"),
                'seq': event.get("seq", i),
                'collection': event.get("$type", "com.example.test"),
                'record': encoded_event.get("record", {}),
                'model_dump_json': lambda self: json.dumps({
                    'op': self.op,
                    'seq': self.seq,
                    'collection': self.collection,
                    'record': self.record
                })
            })()
            
            # Call the message handler
            if self.message_handler:
                self.message_handler(message)
                
            # Sleep for the specified delay
            time.sleep(self.event_delay)