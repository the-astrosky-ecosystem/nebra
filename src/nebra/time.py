from datetime import UTC, datetime


def get_atproto_utc_time():
    """Returns a maximally atproto-compatible UTC datetime.
    
    See https://atproto.com/specs/lexicon#datetime
    """
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
