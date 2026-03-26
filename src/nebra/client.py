"""Client for posting objects of an arbitrary schema onto atproto with Python.

Much of this code adapted from https://github.com/the-astrosky-ecosystem/astronomy-feeds
and from the ATProto Python SDK's examples.
"""

import os
from atproto import Client, Session, SessionEvent, models


def send(event: dict, reuse_session: bool = True):
    handle, password, base_url = get_credentials()
    client = get_client(
        handle, password, base_url=base_url, reuse_session=reuse_session
    )

    client.com.atproto.repo.create_record(
        models.ComAtprotoRepoCreateRecord.Data(
            collection=event["$type"], record=event, repo=handle#, validate=True
        )
    )


def get_credentials():
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
    """A standard function for getting a valid client - already logged in and
    ready to go =)
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
        except Exception as e:
            logger.error(f"Unable to log in with previous session! Reason: {e}")

    # We revert to password login if we can't find a session or if there was an issue
    client.login(handle, password)
    return client


def _get_session(handle: str) -> str | None:
    try:
        with open(f"{handle}.session") as f:
            return f.read()
    except FileNotFoundError:
        return None


class BotSessionUpdater:
    def __init__(self, handle):
        """Simple class to save a client's session to a file named {handle}.session."""
        self.handle = handle

    def on_session_change(self, event: SessionEvent, session: Session) -> None:
        """Callback to save session."""
        print(f"Session changed: {repr(event)}, {repr(session)}")
        if event in (SessionEvent.CREATE, SessionEvent.REFRESH):
            self.save_session(session.export())

    def save_session(self, session_string: str) -> None:
        with open(f"{self.handle}.session", "w") as f:
            f.write(session_string)
