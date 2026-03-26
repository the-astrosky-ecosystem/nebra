"""Client to connect to a jetstream instance and stream ATProto events.

Mainly adapted from this code, © Dave Peck (MIT License):
https://gist.github.com/davepeck/5484fc026a2e8269cf1ead00fff0ef8f
"""

import os
import platform
import typing as t
from pathlib import Path
from urllib.parse import urlencode
import zstandard as zstd
import json
from httpx_ws import connect_ws
from atproto import IdResolver
import click


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
    "--instance",
    "-i",
    help="If using a Bluesky PBC Jetstream instance, choose which public Jetstream instance number to connect to. Currently, 1 and 2 are available.",
    type=int,
    default=1,
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
    instance: int = 1,
    compress: bool = True,
):
    """Emit Jetstream JSON messages to the console, one per line."""
    print(f"Fetching DIDs for handles {handles}")

    # Resolve handles and form the final list of DIDs to subscribe to.
    handle_dids = [resolve_handle_to_did(handle) for handle in handles]
    dids = list(dids) + handle_dids

    # Build the Zstandard decompressor if compression is enabled.
    decompressor = get_zstd_decompressor() if compress else None

    # Form the Jetstream URL to connect to.
    base_url = base_url or get_public_jetstream_base_url(geo, instance)
    url = get_jetstream_query_url(base_url, collections, dids, cursor, compress)

    print(f"Subscription URL: {url}")

    print("Subscribing to jetstream...")
    with connect_ws(url) as ws:
        while True:
            if decompressor:
                message = ws.receive_bytes()
                with decompressor.stream_reader(message) as reader:
                    message = reader.read()
                message = message.decode("utf-8")
            else:
                message = ws.receive_text()

            message = json.loads(message)
            print(message)
            # print(message["time_us"])


PUBLIC_URL_FMT = "wss://jetstream{instance}.{geo}.bsky.network/subscribe"


def get_public_jetstream_base_url(
    geo: t.Literal["us-west", "us-east"] = "us-east",
    instance: int = 1,
) -> str:
    """Return a public Jetstream URL with the given options."""
    return PUBLIC_URL_FMT.format(geo=geo, instance=instance)


def get_jetstream_query_url(
    base_url: str,
    collections: t.Sequence[str],
    dids: t.Sequence[str],
    cursor: int,
    compress: bool,
) -> str:
    """Return a Jetstream URL with the given query parameters."""
    query = [("wantedCollections", collection) for collection in collections]
    query += [("wantedDids", did) for did in dids]
    if cursor:  # Only include the cursor if it is non-zero.
        query.append(("cursor", str(cursor)))
    if compress:
        query.append(("compress", "true"))
    query_enc = urlencode(query, safe=":.*")
    return f"{base_url}?{query_enc}" if query_enc else base_url


#
# Utilities to manage zstd decompression of data (use the --compress flag to enable)
#

# Jetstream uses a custom zstd dict to improve compression; here's where to find it:
ZSTD_DICT_URL = "https://raw.githubusercontent.com/bluesky-social/jetstream/main/pkg/models/zstd_dictionary"


def get_cache_directory(app_name: str) -> Path:
    """
    Determines the appropriate cache directory for the application, cross-platform.

    Args:
        app_name (str): The name of your application.

    Returns:
        Path: The path to the cache directory.
    """
    if platform.system() == "Windows":
        # Use %LOCALAPPDATA% for Windows
        base_cache_dir = os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")
    else:
        # Use XDG_CACHE_HOME or fallback to ~/.cache for Unix-like systems
        base_cache_dir = os.getenv("XDG_CACHE_HOME", Path.home() / ".cache")

    cache_dir = Path(base_cache_dir) / app_name
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def download_zstd_dict(zstd_dict_path: Path):
    """
    Download the Zstandard dictionary from the Jetstream repository.

    Args:
        zstd_dict_path (Path): The path to save the Zstandard dictionary.
    """
    import httpx

    with httpx.stream("GET", ZSTD_DICT_URL) as response:
        with zstd_dict_path.open("wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)


def get_zstd_decompressor() -> zstd.ZstdDecompressor:
    """Get a Zstandard decompressor with a pre-trained dictionary."""
    cache_dir = get_cache_directory("jetstream")
    cache_dir.mkdir(parents=True, exist_ok=True)
    zstd_dict_path = cache_dir / "zstd_dict.bin"

    if not zstd_dict_path.exists():
        download_zstd_dict(zstd_dict_path)

    with zstd_dict_path.open("rb") as f:
        zstd_dict = f.read()

    dict_data = zstd.ZstdCompressionDict(zstd_dict)
    return zstd.ZstdDecompressor(dict_data=dict_data)


# Pre-cached ID resolver
_ID_RESOLVER = IdResolver()


def resolve_handle_to_did(handle: str) -> str | None:
    """Resolves an ATProto handle, like @bsky.app, to a DID."""
    return _ID_RESOLVER.handle.resolve(handle)
