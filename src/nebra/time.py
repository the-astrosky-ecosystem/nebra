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
