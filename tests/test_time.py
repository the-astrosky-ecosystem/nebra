# tests/test_time.py

from datetime import UTC, datetime
from unittest.mock import patch

from nebra.time import get_atproto_utc_time


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