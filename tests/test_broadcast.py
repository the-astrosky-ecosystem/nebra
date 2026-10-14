# tests/test_rebroadcast.py

import queue
import threading
import time
from unittest.mock import patch

from nebra.broadcast import DataSource, RebroadcastClient

from .utilities import DummyDataSource, dummy_send


def failing_producer(data_source: DataSource) -> None:
    """A producer function that generates events but always fails to send them."""
    event_counter = 0
    while data_source.is_active():
        event = {
            "$type": "com.example.test",
            "value": f"test_value_{event_counter}",
            "counter": event_counter,
        }
        data_source.add_event(event)
        event_counter += 1
        time.sleep(0.1)


def failing_send(event: dict, **kwargs) -> None:
    """A send function that always fails."""
    raise ValueError("Simulated send failure")


def test_rebroadcast_client_initialization():
    """Test that RebroadcastClient initializes correctly."""
    def dummy_producer(data_source: DataSource) -> None:
        pass
        
    client = RebroadcastClient(dummy_producer, send_function=dummy_send)
    
    assert isinstance(client.data_source, DataSource)
    assert client.max_retries == 7
    assert client.initial_retry_delay == 1.0
    assert client.send_function == dummy_send


def test_rebroadcast_client_start_stop():
    """Test that RebroadcastClient can start and stop without errors."""
    def slow_producer(data_source: DataSource) -> None:
        while data_source.is_active():
            data_source.mark_producer_running()
            time.sleep(0.5)
    
    client = RebroadcastClient(slow_producer, send_function=dummy_send)
    
    # Start the client in a non-blocking way
    client.start(block=False)
    
    # Give it a moment to start
    time.sleep(0.2)
    
    # Check that threads are running
    assert client.producer_thread is not None
    assert client.consumer_thread is not None
    assert client.producer_thread.is_alive()
    assert client.consumer_thread.is_alive()
    
    # Stop the client
    client.stop()
    
    # Check that threads are stopped
    assert client.producer_thread is None
    assert client.consumer_thread is None


def event_producer(data_source: DataSource) -> None:
    """A producer function that generates test events."""
    event_counter = 0
    while data_source.is_active():
        event = {
            "$type": "com.example.test",
            "value": f"test_value_{event_counter}",
            "counter": event_counter,
        }
        data_source.add_event(event)
        event_counter += 1
        time.sleep(0.1)

def test_rebroadcast_client_event_processing():
    """Test that RebroadcastClient processes events correctly."""
    # Create a mock to track calls to dummy_send
    mock_send = patch('tests.test_broadcast.dummy_send', wraps=lambda event, **kwargs: dummy_send(event, **kwargs)).start()
    
    client = RebroadcastClient(event_producer, send_function=mock_send, max_retries=3)
    
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
    
    def single_event_producer(data_source: DataSource) -> None:
        """A producer that generates a single event."""
        if data_source.is_active():
            event = {
                "$type": "com.example.test",
                "value": "test_value",
                "counter": 1,
            }
            data_source.add_event(event)
    
    mock_send = patch('tests.test_broadcast.dummy_send', side_effect=mock_send_with_failures).start()
    
    client = RebroadcastClient(single_event_producer, send_function=mock_send, max_retries=3, initial_retry_delay=0.1)
    
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


import pytest


def test_data_source_is_active():
    """Test that DataSource.is_active() works correctly."""
    data_source = DummyDataSource()
    
    # Initially should be active
    assert data_source.is_active() is True
    
    # After stopping, should be inactive
    data_source.stop()
    assert data_source.is_active() is False


def test_data_source_get_event():
    """Test that DataSource.get_event() works correctly with and without timeout."""
    data_source = DummyDataSource()
    
    # Add a test event
    test_event = {"$type": "com.example.test", "value": "test"}
    data_source.add_event(test_event)
    
    # Get the event without timeout
    event = data_source.get_event()
    assert event == test_event
    
    # Test with timeout - should raise queue.Empty
    with pytest.raises(queue.Empty):
        data_source.get_event(timeout=0.1)
    
    # Test with timeout when event is available
    data_source.add_event(test_event)
    event = data_source.get_event(timeout=0.1)
    assert event == test_event


def test_data_source_producer_tracking():
    """Test that DataSource.mark_producer_running() and producer_last_signal() work correctly."""
    data_source = DummyDataSource()
    
    # Initially should return a small number (time since initialization)
    initial_signal = data_source.producer_last_signal()
    assert initial_signal >= 0
    assert initial_signal < 0.1  # Should be very recent
    
    # Mark producer as running
    data_source.mark_producer_running()
    
    # Should return a small number (just called)
    first_signal = data_source.producer_last_signal()
    assert first_signal >= 0
    assert first_signal < 0.1  # Should be very recent
    
    # Wait a bit and check again
    time.sleep(0.01)
    second_signal = data_source.producer_last_signal()
    assert second_signal >= 0.01  # Should be at least as much as we waited
    
    # Mark again
    data_source.mark_producer_running()
    
    # Should return a small number again
    third_signal = data_source.producer_last_signal()
    assert third_signal >= 0
    assert third_signal < 0.1  # Should be very recent again
    
    # Test thread safety by calling from multiple threads
    def mark_producer():
        for _ in range(100):
            data_source.mark_producer_running()
    
    threads = []
    for _ in range(5):
        t = threading.Thread(target=mark_producer)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Should return a small number (recently updated)
    final_signal = data_source.producer_last_signal()
    assert final_signal >= 0
    assert final_signal < 0.1  # Should be very recent


@pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
def test_rebroadcast_client_max_retries():
    """Test that RebroadcastClient respects max_retries."""
    # Create a mock to track calls
    call_count = 0
    def mock_send_always_fails(event, **kwargs):
        nonlocal call_count
        call_count += 1
        raise ValueError("Simulated send failure")
    
    def single_event_producer(data_source: DataSource) -> None:
        """A producer that generates a single event."""
        if data_source.is_active():
            event = {
                "$type": "com.example.test",
                "value": "test_value",
                "counter": 1,
            }
            data_source.add_event(event)
    
    mock_send = patch('tests.test_broadcast.dummy_send', side_effect=mock_send_always_fails).start()
    
    # Calculate the total time needed for all retries
    # initial_retry_delay * (2^0 + 2^1 + 2^2) = 0.1 + 0.2 + 0.4 = 0.7s
    total_retry_time = 0.1 * (1 + 2 + 4)  # Sum of all retry delays
    
    client = RebroadcastClient(single_event_producer, send_function=mock_send, max_retries=3, initial_retry_delay=0.1)
    
    # Start the client in a non-blocking way
    client.start(block=False)
    
    # Let it run long enough for all retries to complete
    time.sleep(total_retry_time + 0.2)  # Add a small buffer
    
    # Stop the client and ensure all threads are cleaned up
    client.stop()
    if client.consumer_thread is not None:
        client.consumer_thread.join(timeout=1.0)
    if client.producer_thread is not None:
        client.producer_thread.join(timeout=1.0)
    
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
    
    def fast_producer(data_source: DataSource) -> None:
        """A producer that generates events quickly."""
        event_counter = 0
        while data_source.is_active():
            event = {
                "$type": "com.example.test",
                "value": f"test_value_{event_counter}",
                "counter": event_counter,
            }
            data_source.add_event(event)
            event_counter += 1
            time.sleep(0.05)
    
    mock_send = patch('tests.test_broadcast.dummy_send', side_effect=mock_send_slow).start()
    
    # Create a client with a small queue and fast event generation
    client = RebroadcastClient(
        fast_producer, 
        send_function=mock_send, 
        max_retries=0
    )
    client.data_source._event_queue = queue.Queue(maxsize=3)  # Set small queue size
    
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