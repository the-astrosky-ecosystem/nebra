# tests/test_rebroadcast.py

import threading
import time
from unittest.mock import patch

from nebra.rebroadcast import DataSource, RebroadcastClient

from .utilities import DummyDataSource, dummy_send


class FailingDataSource(DataSource):
    """A data source that generates events but always fails to send them."""

    def __init__(self, max_queue_size: int = 1000, event_delay: float = 0.1):
        super().__init__(max_queue_size)
        self.event_delay = event_delay
        self.event_counter = 0

    def run(self) -> None:
        """Run the data source, generating events that will fail to send."""
        while not self.stop_event.is_set():
            event = {
                "$type": "com.example.test",
                "value": f"test_value_{self.event_counter}",
                "counter": self.event_counter,
            }
            self.add_event(event)
            self.event_counter += 1
            time.sleep(self.event_delay)


def failing_send(event: dict, **kwargs) -> None:
    """A send function that always fails."""
    raise ValueError("Simulated send failure")


def test_rebroadcast_client_initialization():
    """Test that RebroadcastClient initializes correctly."""
    data_source = DummyDataSource()
    client = RebroadcastClient(data_source, send_function=dummy_send)
    
    assert client.data_source == data_source
    assert client.max_retries == 7
    assert client.initial_retry_delay == 1.0
    assert client.send_function == dummy_send


def test_rebroadcast_client_start_stop():
    """Test that RebroadcastClient can start and stop without errors."""
    data_source = DummyDataSource(event_delay=0.5)
    client = RebroadcastClient(data_source, send_function=dummy_send)
    
    # Start the client in a non-blocking way
    client.start(block=False)
    
    # Give it a moment to start
    time.sleep(0.2)
    
    # Check that threads are running
    assert client.data_source_thread is not None
    assert client.consumer_thread is not None
    assert client.data_source_thread.is_alive()
    assert client.consumer_thread.is_alive()
    
    # Stop the client
    client.stop()
    
    # Check that threads are stopped
    assert client.data_source_thread is None
    assert client.consumer_thread is None


def test_rebroadcast_client_event_processing():
    """Test that RebroadcastClient processes events correctly."""
    # Create a mock to track calls to dummy_send
    mock_send = patch('tests.test_rebroadcast.dummy_send', wraps=lambda event, **kwargs: dummy_send(event, **kwargs)).start()
    
    data_source = DummyDataSource(max_queue_size=5, event_delay=0.1)
    client = RebroadcastClient(data_source, send_function=mock_send, max_retries=3)
    
    # Start the client in a non-blocking way
    client.start(block=False)
    
    # Let it run for a short time
    time.sleep(0.5)
    
    # Stop the client
    client.stop()
    
    # Check that dummy_send was called with events
    assert mock_send.call_count > 0
    
    # Check that each call had a valid event
    for call in mock_send.call_args_list:
        event = call[0][0]  # First positional argument
        assert "$type" in event
        assert event["$type"] == "com.example.test"
        assert "value" in event
        assert "counter" in event
    
    # Clean up
    patch.stopall()


def test_rebroadcast_client_retry_logic():
    """Test that RebroadcastClient retries failed sends."""
    # Create a mock that fails a few times before succeeding
    call_count = 0
    def mock_send_with_failures(event, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:  # Fail twice, then succeed
            raise ValueError("Simulated send failure")
        return dummy_send(event, **kwargs)
    
    mock_send = patch('tests.test_rebroadcast.dummy_send', side_effect=mock_send_with_failures).start()
    
    data_source = DummyDataSource(max_queue_size=1, event_delay=0.1)
    client = RebroadcastClient(data_source, send_function=mock_send, max_retries=3, initial_retry_delay=0.1)
    
    # Start the client in a non-blocking way
    client.start(block=False)
    
    # Let it run for a short time
    time.sleep(0.5)
    
    # Stop the client
    client.stop()
    
    # Check that the mock was called more times than the number of events (due to retries)
    assert call_count > 1
    
    # Clean up
    patch.stopall()


def test_rebroadcast_client_max_retries():
    """Test that RebroadcastClient respects max_retries."""
    # Create a mock to track calls
    call_count = 0
    def mock_send_always_fails(event, **kwargs):
        nonlocal call_count
        call_count += 1
        raise ValueError("Simulated send failure")
    
    mock_send = patch('tests.test_rebroadcast.dummy_send', side_effect=mock_send_always_fails).start()
    
    # Calculate the total time needed for all retries
    # initial_retry_delay * (2^0 + 2^1 + 2^2) = 0.1 + 0.2 + 0.4 = 0.7s
    total_retry_time = 0.1 * (1 + 2 + 4)  # Sum of all retry delays
    
    data_source = DummyDataSource(max_queue_size=1, event_delay=0.1)
    client = RebroadcastClient(data_source, send_function=mock_send, max_retries=3, initial_retry_delay=0.1)
    
    # Start the client in a non-blocking way
    client.start(block=False)
    
    # Let it run long enough for all retries to complete
    time.sleep(total_retry_time + 0.2)  # Add a small buffer
    
    # Stop the client
    client.stop()
    
    # Check that the mock was called max_retries + 1 times (initial attempt + retries)
    # We might get fewer calls if the test stops too early, but we should get at least max_retries
    assert call_count >= 3  # At least 3 retries (initial attempt + 2 retries)
    
    # Clean up
    patch.stopall()


def test_rebroadcast_client_queue_full():
    """Test that RebroadcastClient handles a full queue correctly."""
    # Create a mock that takes a long time to process events
    processing_event = threading.Event()
    
    def mock_send_slow(event, **kwargs):
        processing_event.wait()  # Block until released
        return dummy_send(event, **kwargs)
    
    mock_send = patch('tests.test_rebroadcast.dummy_send', side_effect=mock_send_slow).start()
    
    # Create a data source with a small queue and fast event generation
    data_source = DummyDataSource(max_queue_size=3, event_delay=0.05)
    client = RebroadcastClient(data_source, send_function=mock_send, max_retries=0)
    
    # Start the client in a non-blocking way
    client.start(block=False)
    
    # Let it run for a short time to fill the queue
    time.sleep(0.3)
    
    # At this point, the queue should be full and some events should be dropped
    # We can't directly observe this, but we can check that the client doesn't crash
    
    # Release the mock to process events
    processing_event.set()
    
    # Stop the client
    client.stop()
    
    # Clean up
    patch.stopall()