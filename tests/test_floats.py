# tests/test_floats.py

from nebra.floats import decode_floats_in_event, encode_floats_in_event


def test_encode_floats_in_event():
    """Test that encode_floats_in_event correctly encodes floating point numbers."""
    # Test with a simple event
    event = {
        "value": 3.14,
        "nested": {
            "float_list": [1.0, 2.5, 3.7],
            "mixed_list": ["text", 4.2, True],
            "other": "string"
        },
        "integer": 42,
        "string": "hello"
    }
    
    encoded_event = encode_floats_in_event(event)
    
    # Check that all floats are encoded
    assert encoded_event["value"] == "№3.14№"
    assert encoded_event["nested"]["float_list"] == ["№1.0№", "№2.5№", "№3.7№"]
    assert encoded_event["nested"]["mixed_list"] == ["text", "№4.2№", True]
    assert encoded_event["integer"] == 42  # Integers should be unchanged
    assert encoded_event["string"] == "hello"  # Strings should be unchanged


def test_decode_floats_in_event():
    """Test that decode_floats_in_event correctly decodes encoded floating point numbers."""
    # Test with an encoded event
    encoded_event = {
        "value": "№3.14№",
        "nested": {
            "float_list": ["№1.0№", "№2.5№", "№3.7№"],
            "mixed_list": ["text", "№4.2№", True],
            "other": "string"
        },
        "integer": 42,
        "string": "hello"
    }
    
    decoded_event = decode_floats_in_event(encoded_event)
    
    # Check that all encoded floats are decoded
    assert decoded_event["value"] == 3.14
    assert decoded_event["nested"]["float_list"] == [1.0, 2.5, 3.7]
    assert decoded_event["nested"]["mixed_list"] == ["text", 4.2, True]
    assert decoded_event["integer"] == 42  # Integers should be unchanged
    assert decoded_event["string"] == "hello"  # Strings should be unchanged


def test_round_trip_conversion():
    """Test that encoding and then decoding an event returns the original event."""
    # Original event with various data types
    original_event = {
        "float_value": 3.14159,
        "nested": {
            "float_list": [1.0, 2.5, 3.7],
            "mixed_data": ["text", 42, 4.2, True, None],
            "deep_nested": {
                "another_float": 2.718,
                "string_with_numbers": "123.456"
            }
        },
        "integer": 42,
        "string": "hello",
        "boolean": True,
        "none": None
    }
    
    # Encode and then decode the event
    encoded_event = encode_floats_in_event(original_event)
    decoded_event = decode_floats_in_event(encoded_event)
    
    # The decoded event should match the original
    assert decoded_event == original_event


def test_non_float_strings_with_markers():
    """Test that strings with № markers that aren't floats are left unchanged."""
    event = {
        "valid_float": "№3.14№",
        "invalid_float": "№not_a_number№",
        "string_with_marker": "This has a № marker",
        "normal_string": "Just text"
    }
    
    decoded_event = decode_floats_in_event(event)
    
    # Valid float should be decoded
    assert decoded_event["valid_float"] == 3.14
    
    # Invalid float should remain as a string
    assert decoded_event["invalid_float"] == "№not_a_number№"
    
    # Other strings should be unchanged
    assert decoded_event["string_with_marker"] == "This has a № marker"
    assert decoded_event["normal_string"] == "Just text"