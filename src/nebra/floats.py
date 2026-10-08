"""Module for handling floating point numbers in ATProtocol records.

ATProtocol doesn't support floating point numbers directly, so this module provides
functions to convert floats to specially formatted strings and back again.
"""

import re
from typing import Any

# Special marker for encoded floats
FLOAT_MARKER = "№"
FLOAT_PATTERN = re.compile(rf"^{re.escape(FLOAT_MARKER)}(.+?){re.escape(FLOAT_MARKER)}$")


def encode_floats_in_event(event: dict[str, Any]) -> dict[str, Any]:
    """Recursively encode all floating point numbers in an event as specially marked strings.
    
    Args:
        event: The event dictionary to process.
        
    Returns:
        A new dictionary with all floating point numbers encoded as strings.
    """
    return _encode_floats_recursive(event)


def decode_floats_in_event(event: dict[str, Any]) -> dict[str, Any]:
    """Recursively decode all specially marked strings in an event back to floating point numbers.
    
    Args:
        event: The event dictionary to process.
        
    Returns:
        A new dictionary with all encoded strings converted back to floating point numbers.
    """
    return _decode_floats_recursive(event)


def _encode_floats_recursive(data: Any) -> Any:
    """Recursively encode floating point numbers in a data structure."""
    if isinstance(data, float):
        # Encode the float as a specially marked string
        return f"{FLOAT_MARKER}{data}{FLOAT_MARKER}"
    elif isinstance(data, dict):
        # Process each value in the dictionary
        return {key: _encode_floats_recursive(value) for key, value in data.items()}
    elif isinstance(data, (list, tuple)):
        # Process each item in the list/tuple
        return [_encode_floats_recursive(item) for item in data]
    else:
        # Return other types unchanged
        return data


def _decode_floats_recursive(data: Any) -> Any:
    """Recursively decode specially marked strings in a data structure."""
    if isinstance(data, str):
        # Check if the string is a specially marked float
        match = FLOAT_PATTERN.match(data)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                # If conversion fails, return the original string
                return data
        return data
    elif isinstance(data, dict):
        # Process each value in the dictionary
        return {key: _decode_floats_recursive(value) for key, value in data.items()}
    elif isinstance(data, (list, tuple)):
        # Process each item in the list/tuple
        return [_decode_floats_recursive(item) for item in data]
    else:
        # Return other types unchanged
        return data