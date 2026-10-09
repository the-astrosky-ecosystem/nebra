"""Client to connect to a jetstream instance and stream ATProto events."""

import json
import typing as t
from collections.abc import Callable

import click
from atproto import IdResolver
from atproto_client.models import NetworkBskyJetstreamSubscribeEvents
from atproto_jetstream import (
    JetstreamClient,
    SubscribeEventsMessage,
)

from nebra.floats import decode_floats_in_event


def _run_stream(
    collections: t.Sequence[str] = (),
    dids: t.Sequence[str] = (),
    handles: t.Sequence[str] = (),
    message_handler: Callable = print,
    cursor: int = 0,
    base_url: str | None = None,
    geo: t.Literal["us-west", "us-east"] = "us-west",
    compress: bool = True,
    kinds: t.Sequence[str] = ("commit",),
    client_factory: t.Callable[..., JetstreamClient] = JetstreamClient,
) -> None:
    """Run the stream with the given parameters.

    Parameters
    ----------
    collections : Sequence[str], optional
        The collections to subscribe to. Defaults to empty tuple.
    dids : Sequence[str], optional
        The DIDs to subscribe to. Defaults to empty tuple.
    handles : Sequence[str], optional
        The ATProto handles to subscribe to. Defaults to empty tuple.
    message_handler : Callable[[str], None], optional
        Function to handle incoming messages. Defaults to print.
    cursor : int, optional
        The cursor to start from. Defaults to 0.
    base_url : str, optional
        The Jetstream URL to connect to. Defaults to None.
    geo : {"us-west", "us-east"}, optional
        The geography to use for public Jetstream. Defaults to "us-west".
    compress : bool, optional
        Whether to enable compression. Defaults to True.
    kinds : Sequence[str], optional
        The kinds of events to subscribe to. Defaults to ("commit",).
    client_factory : Callable[..., JetstreamClient], optional
        Factory function to create the Jetstream client. Defaults to JetstreamClient.
        
    Returns
    -------
    None
        This function does not return a value.
    """
    print(f"Fetching DIDs for handles {handles}")

    # Resolve handles and form the final list of DIDs to subscribe to.
    handle_dids = [resolve_handle_to_did(handle) for handle in handles]
    all_dids = [did for did in [*dids, *handle_dids] if did is not None]

    # Build the Jetstream params to subscribe with.
    params: NetworkBskyJetstreamSubscribeEvents.ParamsDict = {"kinds": list(kinds)}
    if collections:
        params["collections"] = list(collections)
    if all_dids:
        params["dids"] = all_dids
    if cursor:
        # Only include the cursor if it is non-zero.
        params["cursor"] = cursor

    # Form the Jetstream base URI to connect to.
    base_uri = base_url or get_public_jetstream_base_uri(geo)

    print(f"Subscribing to jetstream at {base_uri}...")

    client = client_factory(
        params=params,
        base_uri=base_uri,
        compress=compress,
    )

    def on_message(message: SubscribeEventsMessage) -> None:
        # Parse the JSON message before decoding: decode_floats_in_event can't
        # reach encoded floats inside a raw JSON string, only inside a dict/list.
        decoded = decode_floats_in_event(message.model_dump(mode="json"))
        message_handler(decoded)

    client.start(on_message)


def stream(
    collections: t.Sequence[str] = (),
    dids: t.Sequence[str] = (),
    handles: t.Sequence[str] = (),
    message_handler: Callable = print,
    cursor: int = 0,
    base_url: str | None = None,
    geo: t.Literal["us-west", "us-east"] = "us-west",
    compress: bool = True,
    kinds: t.Sequence[str] = ("commit",),
) -> None:
    """Programmatic interface for streaming Jetstream messages.
    
    This function streams Jetstream messages and passes them to the provided
    `message_handler`. It can be called directly from Python code.
    
    Parameters
    ----------
    collections : Sequence[str], optional
        The collections to subscribe to. Defaults to empty tuple.
    dids : Sequence[str], optional
        The DIDs to subscribe to. Defaults to empty tuple.
    handles : Sequence[str], optional
        The ATProto handles to subscribe to. Defaults to empty tuple.
    message_handler : Callable[[str], None], optional
        Function to handle incoming messages. Defaults to print.
    cursor : int, optional
        The cursor to start from. Defaults to 0.
    base_url : str, optional
        The Jetstream URL to connect to. Defaults to None.
    geo : {"us-west", "us-east"}, optional
        The geography to use for public Jetstream. Defaults to "us-west".
    compress : bool, optional
        Whether to enable compression. Defaults to True.
    kinds : Sequence[str], optional
        The kinds of events to subscribe to. Defaults to ("commit",).
    """
    _run_stream(
        collections=collections,
        dids=dids,
        handles=handles,
        message_handler=message_handler,
        cursor=cursor,
        base_url=base_url,
        geo=geo,
        compress=compress,
        kinds=kinds,
    )


# Define the options as a list of dictionaries
options = [
    {
        "args": ["--collections", "-c"],
        "kwargs": {
            "multiple": True,
            "help": "The collections to subscribe to. If not provided, subscribe to all.",
            "type": str,
            "default": ("eco.astrosky.transient.*",),
        },
    },
    {
        "args": ["--dids", "-d"],
        "kwargs": {
            "multiple": True,
            "help": "The DIDs to subscribe to. If not provided, subscribe to all.",
            "type": str,
            "default": (),
        },
    },
    {
        "args": ["--handles", "-h"],
        "kwargs": {
            "multiple": True,
            "help": "The ATProto handles to subscribe to. If not provided, subscribe to all.",
            "type": str,
            "default": (),
        },
    },
    {
        "args": ["--cursor", "-u"],
        "kwargs": {
            "help": "The cursor to start from. If not provided or set to zero, start from 'now'. Note that the cursor can only go as far back as the Jetstream instance has indexed.",
            "type": int,
            "default": 0,
        },
    },
    {
        "args": ["--base-url"],
        "kwargs": {
            "help": "The Jetstream URL to connect to.",
            "type": str,
        },
    },
    {
        "args": ["--geo", "-g"],
        "kwargs": {
            "help": "If using a Bluesky PBC Jetstream instance, choose which public Jetstream service geography to connect to.",
            "type": click.Choice(["us-west", "us-east"]),
            "default": "us-east",
        },
    },
    {
        "args": ["--compress"],
        "kwargs": {
            "is_flag": True,
            "help": "Enable Zstandard compression.",
            "default": True,
        },
    },
    {
        "args": ["--kinds"],
        "kwargs": {
            "multiple": True,
            "help": "The event kinds to subscribe to (e.g., 'commit', 'identity'). Defaults to 'commit'.",
            "type": str,
            "default": ["commit"],
        },
    },
]

# Define the base command
stream_command = click.command(name="stream")(stream)

# Apply the options in a loop
for option in options:
    stream_command = click.option(*option["args"], **option["kwargs"])(stream_command)


PUBLIC_URI_FMT = "wss://jetstream.{geo}.bsky.network/xrpc"


def get_public_jetstream_base_uri(
    geo: t.Literal["us-west", "us-east"] = "us-east",
) -> str:
    """Get a public Jetstream base URI for the specified geography.
    
    Parameters
    ----------
    geo : {"us-west", "us-east"}, optional
        The geography to use for the public Jetstream service. Defaults to us-east.
        
    Returns
    -------
    str
        The base URI for the specified geography.
    """
    return PUBLIC_URI_FMT.format(geo=geo)


# Pre-cached ID resolver
_ID_RESOLVER = IdResolver()


def resolve_handle_to_did(handle: str) -> str | None:
    """Resolve an ATProto handle to a DID.
    
    Parameters
    ----------
    handle : str
        The ATProto handle to resolve (e.g., "@bsky.app").
        
    Returns
    -------
    str or None
        The resolved DID if successful, None if resolution fails.
    """
    return _ID_RESOLVER.handle.resolve(handle)
