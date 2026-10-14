from datetime import UTC, datetime


def get_atproto_utc_time():
    """Get a maximally ATProto-compatible UTC datetime string.
    
    This function returns a datetime string in the format specified by the ATProtocol
    lexicon, which is "YYYY-MM-DDTHH:MM:SS.sssZ".
    
    Returns
    -------
    str
        A datetime string in ATProtocol-compatible format.
        
    See Also
    --------
    https://atproto.com/specs/lexicon#datetime : ATProtocol datetime specification
    """
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def atproto_timestamp_to_datetime(timestamp: str) -> datetime:
    """Convert an ATProto timestamp string to a Python datetime object.
    
    ATProto timestamps are a subset of ISO 8601/RFC 3339, with the format
    "YYYY-MM-DDTHH:MM:SS.sssZ". This function parses the timestamp and returns
    a timezone-aware datetime object in UTC.
    
    Parameters
    ----------
    timestamp : str
        An ATProto timestamp string (e.g., "1985-04-12T23:20:50.123Z").
    
    Returns
    -------
    datetime
        A timezone-aware datetime object in UTC.
        
    Raises
    ------
    ValueError
        If the timestamp is not in the expected format or violates ATProto rules.
        
    See Also
    --------
    https://atproto.com/specs/lexicon#datetime : ATProtocol datetime specification
    """
    # Reject invalid timezone formats
    if timestamp.endswith('-00:00'):
        raise ValueError("ATProto timestamps cannot use '-00:00' timezone")
    
    # Replace the 'Z' suffix with '+00:00' to make it compatible with fromisoformat
    if timestamp.endswith('Z'):
        iso_timestamp = timestamp[:-1] + '+00:00'
    else:
        iso_timestamp = timestamp
    
    # Parse the timestamp and ensure it is timezone-aware
    dt = datetime.fromisoformat(iso_timestamp)
    if dt.tzinfo is None:
        raise ValueError("ATProto timestamps must include a timezone")
    
    # Convert to UTC for consistency
    return dt.astimezone(UTC)
