# tests/test_time.py

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from nebra.time import atproto_timestamp_to_datetime, get_atproto_utc_time


def test_get_atproto_utc_time():
    """Test that get_atproto_utc_time returns the correct format."""
    # Mock datetime.now() to return a fixed time
    fixed_time = datetime(2023, 1, 1, 12, 0, 0, 123456, UTC)
    with patch("nebra.time.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_time
        mock_datetime.UTC = UTC
        
        result = get_atproto_utc_time()
        
    # Check the result matches the expected format
    expected = "2023-01-01T12:00:00.123456Z"
    assert result == expected


def test_get_datetime_from_atproto_timestamp():
    """Test that get_datetime_from_atproto_timestamp correctly parses ATProto timestamps."""
    # Test with 'Z' suffix (UTC)
    timestamp = "1985-04-12T23:20:50.123Z"
    dt = atproto_timestamp_to_datetime(timestamp)
    assert dt.year == 1985
    assert dt.month == 4
    assert dt.day == 12
    assert dt.hour == 23
    assert dt.minute == 20
    assert dt.second == 50
    assert dt.microsecond == 123000  # Truncated to microseconds
    assert dt.tzinfo == UTC
    
    # Test without 'Z' suffix (assumed UTC)
    timestamp_no_z = "1985-04-12T23:20:50.123+00:00"
    dt_no_z = atproto_timestamp_to_datetime(timestamp_no_z)
    assert dt_no_z == dt
    
    # Test with explicit timezone (converted to UTC)
    timestamp_tz = "1985-04-12T19:20:50.123-04:00"
    dt_tz = atproto_timestamp_to_datetime(timestamp_tz)
    assert dt_tz == dt
    
    # Test invalid format raises ValueError
    with pytest.raises(ValueError):
        atproto_timestamp_to_datetime("not-a-timestamp")
    
    # Test '-00:00' timezone raises ValueError
    with pytest.raises(ValueError, match="-00:00"):
        atproto_timestamp_to_datetime("1985-04-12T23:20:50.123-00:00")
    
    # Test missing timezone raises ValueError
    with pytest.raises(ValueError, match="timezone"):
        atproto_timestamp_to_datetime("1985-04-12T23:20:50.123")