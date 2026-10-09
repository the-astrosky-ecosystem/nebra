"""Client for posting objects of an arbitrary schema onto atproto with Python.

Much of this code adapted from https://github.com/the-astrosky-ecosystem/astronomy-feeds
and from the ATProto Python SDK's examples.
"""

import os

from atproto import Client, Session, SessionEvent, models
from atproto.exceptions import AtProtocolError

from nebra.floats import encode_floats_in_event


def send(event: dict, reuse_session: bool = True):
    """Send an event to the AT Protocol.

    Parameters
    ----------
    event : dict
        The event to send, which must include a "$type" field.
    reuse_session : bool, optional
        Whether to reuse an existing session if available. Defaults to True.

    Returns
    -------
    None
        This function does not return a value.
    """
    handle, password, base_url = get_credentials()
    client = get_client(
        handle, password, base_url=base_url, reuse_session=reuse_session
    )

    # Encode floating point numbers before sending
    encoded_event = encode_floats_in_event(event)
    
    client.com.atproto.repo.create_record(
        models.ComAtprotoRepoCreateRecord.Data(
            collection=encoded_event["$type"], record=encoded_event, repo=handle#, validate=True
        )
    )


def get_credentials():
    """Get credentials from environment variables.

    Returns
    -------
    tuple
        A tuple containing (handle, password, base_url).
        
    Raises
    ------
    ValueError
        If NEBRA_HANDLE or NEBRA_PASSWORD environment variables are not set.
    """
    handle = os.getenv("NEBRA_HANDLE")
    if handle is None:
        raise ValueError("You must set the NEBRA_HANDLE environment variable.")
    password = os.getenv("NEBRA_PASSWORD")
    if password is None:
        raise ValueError("You must set the NEBRA_PASSWORD environment variable.")

    base_url = os.getenv("NEBRA_BASE_URL")

    return handle, password, base_url


def get_client(
    handle: str, password: str, base_url: str | None = None, reuse_session: bool = True
) -> Client:
    """Get a logged-in ATProto client.

    Parameters
    ----------
    handle : str
        The handle to log in with.
    password : str
        The password to log in with.
    base_url : str, optional
        The base URL of the ATProto server. Defaults to None.
    reuse_session : bool, optional
        Whether to reuse an existing session if available. Defaults to True.
        
    Returns
    -------
    Client
        A logged-in ATProto client.
    """
    # Set up client and set it up to save its session incrementally
    client = Client(base_url=base_url)
    session_updater = BotSessionUpdater(handle)
    client.on_session_change(session_updater.on_session_change)

    # Login using previous session
    session = _get_session(handle)
    if session and reuse_session:
        try:
            client.login(session_string=session)
            return client
        except AtProtocolError as e:
            print(f"Unable to log in with previous session! Reason: {e}")

    # We revert to password login if we can't find a session or if there was an issue
    client.login(handle, password)
    return client


def _get_session(handle: str) -> str | None:
    """Get a saved session for the given handle.
    
    Parameters
    ----------
    handle : str
        The handle to get the session for.
        
    Returns
    -------
    str or None
        The session string if a saved session exists, None otherwise.
    """
    try:
        with open(f"{handle}.session") as f:
            return f.read()
    except FileNotFoundError:
        return None


class BotSessionUpdater:
    """Class to handle session updates and save sessions to disk.
    
    This class saves client sessions to a file named `{handle}.session` whenever
    the session is created or refreshed.
    
    Attributes
    ----------
    handle : str
        The handle associated with the session.
    """
    
    def __init__(self, handle):
        """Initialize the BotSessionUpdater with a handle.
        
        Parameters
        ----------
        handle : str
            The handle associated with the session.
        """
        self.handle = handle

    def on_session_change(self, event: SessionEvent, session: Session) -> None:
        """Handle session change events.
        
        This method is called whenever the session changes. It saves the session
        to disk if the event is a session creation or refresh.
        
        Parameters
        ----------
        event : SessionEvent
            The session event that occurred.
        session : Session
            The current session.
        """
        print(f"Session changed: {event!r}, {session!r}")
        if event in (SessionEvent.CREATE, SessionEvent.REFRESH):
            self.save_session(session.export())

    def save_session(self, session_string: str) -> None:
        """Save the session to disk.
        
        Parameters
        ----------
        session_string : str
            The session string to save.
        """
        with open(f"{self.handle}.session", "w") as f:
            f.write(session_string)
