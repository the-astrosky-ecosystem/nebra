"""Client to connect to a jetstream instance and stream ATProto events."""

import typing as t

import click
from atproto import IdResolver
from atproto_client.models import NetworkBskyJetstreamSubscribeEvents
from atproto_jetstream import JetstreamClient, SubscribeEventsMessage


@click.command()
@click.option(
    "--collection",
    "-c",
    "collections",
    multiple=True,
    help="The collections to subscribe to. If not provided, subscribe to all.",
    type=str,
    default=("eco.astrosky.transient.*",),
)
@click.option(
    "--did",
    "-d",
    "dids",
    multiple=True,
    help="The DIDs to subscribe to. If not provided, subscribe to all.",
    type=str,
    default=tuple(),
)
@click.option(
    "--handle",
    "-h",
    "handles",
    multiple=True,
    help="The ATProto handles to subscribe to. If not provided, subscribe to all.",
    type=str,
    default=tuple(),
)
@click.option(
    "--cursor",
    "-u",
    help="The cursor to start from. If not provided or set to zero, start from 'now'. Note that the cursor can only go as far back as the Jetstream instance has indexed.",
    type=int,
    default=0,
)
@click.option(
    "--url",
    "base_url",
    help="The Jetstream URL to connect to.",
    type=str,
)
@click.option(
    "--geo",
    "-g",
    help="If using a Bluesky PBC Jetstream instance, choose which public Jetstream service geography to connect to.",
    type=click.Choice(["us-west", "us-east"]),
    default="us-east",
)
@click.option(
    "--compress",
    is_flag=True,
    help="Enable Zstandard compression.",
    default=True,
)
def stream(
    collections: t.Sequence[str] = tuple(),
    dids: t.Sequence[str] = tuple(),
    handles: t.Sequence[str] = tuple(),
    cursor: int = 0,
    base_url: str | None = None,
    geo: t.Literal["us-west", "us-east"] = "us-west",
    compress: bool = True,
):
    """Emit Jetstream JSON messages to the console, one per line."""
    print(f"Fetching DIDs for handles {handles}")

    # Resolve handles and form the final list of DIDs to subscribe to.
    handle_dids = [resolve_handle_to_did(handle) for handle in handles]
    all_dids = [did for did in [*dids, *handle_dids] if did is not None]

    # Build the Jetstream params to subscribe with.
    params: NetworkBskyJetstreamSubscribeEvents.ParamsDict = {}
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

    client = JetstreamClient(
        params=params,
        base_uri=base_uri,
        compress=compress,
    )

    def on_message(message: SubscribeEventsMessage) -> None:
        print(message.model_dump_json())

    client.start(on_message)


PUBLIC_URI_FMT = "wss://jetstream.{geo}.bsky.network/xrpc"


def get_public_jetstream_base_uri(
    geo: t.Literal["us-west", "us-east"] = "us-east",
) -> str:
    """Return a public Jetstream base URI with the given options."""
    return PUBLIC_URI_FMT.format(geo=geo)


# Pre-cached ID resolver
_ID_RESOLVER = IdResolver()


def resolve_handle_to_did(handle: str) -> str | None:
    """Resolves an ATProto handle, like @bsky.app, to a DID."""
    return _ID_RESOLVER.handle.resolve(handle)
