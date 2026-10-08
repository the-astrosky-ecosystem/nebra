# tests/utilities.py

import time
from typing import Any

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
    # Check that the event is a dictionary (record must be a dict)
    if not isinstance(event, dict):
        raise TypeError("Event must be a dictionary")
        
    # Check that the event has a $type field
    if "$type" not in event:
        raise ValueError("Event must have a $type field")
    
    # Check that the $type field is a non-empty string
    if not isinstance(event["$type"], str) or not event["$type"].strip():
        raise ValueError("$type field must be a non-empty string")
    
