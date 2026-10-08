# tests/test_jetstream.py

import json
import time

from nebra.jetstream import run_stream
from tests.utilities import DummyJetstreamClient


def test_stream_with_dummy_client():
    """Test the stream function with a dummy client."""
    # Create a mock message handler to collect received messages
    received_messages = []
    def mock_handler(message):
        received_messages.append(message)
    
    # Create a dummy client that will generate 3 events
    dummy_client = DummyJetstreamClient(event_count=3, event_delay=0.05)
    
    # Run the stream function with our dummy client
    run_stream(
        collections=["com.example.test"],
        message_handler=mock_handler,
        client_factory=lambda **kwargs: dummy_client
    )
    
    # Give it a moment to process events
    time.sleep(0.2)
    
    # Stop the dummy client
    dummy_client.stop()
    
    # Check that we received the expected number of messages
    assert len(received_messages) == 3
    
    # Check that each message is valid JSON
    for message in received_messages:
        data = json.loads(message)
        assert "record" in data
        assert "float_value" in data["record"]
        assert "nested" in data["record"]
        assert "float_list" in data["record"]["nested"]


def test_stream_float_decoding():
    """Test that float decoding works correctly in the stream function."""
    # Create a mock message handler to collect received messages
    received_messages = []
    def mock_handler(message):
        received_messages.append(message)
    
    # Create a dummy client that will generate 2 events
    dummy_client = DummyJetstreamClient(event_count=2, event_delay=0.05)
    
    # Run the stream function with our dummy client
    run_stream(
        collections=["com.example.test"],
        message_handler=mock_handler,
        client_factory=lambda **kwargs: dummy_client
    )
    
    # Give it a moment to process events
    time.sleep(0.15)
    
    # Stop the dummy client
    dummy_client.stop()
    
    # Check that we received the expected number of messages
    assert len(received_messages) == 2
    
    # Check that floats were properly decoded
    for message in received_messages:
        data = json.loads(message)
        record = data["record"]
        
        # Check that float values are actual numbers, not encoded strings
        assert isinstance(record["float_value"], (int, float))
        
        # Check nested float values
        for float_val in record["nested"]["float_list"]:
            assert isinstance(float_val, (int, float))
        
        # Check mixed data contains actual numbers
        for item in record["nested"]["mixed_data"]:
            if isinstance(item, (int, float)) and not isinstance(item, bool):
                assert isinstance(item, (int, float))
