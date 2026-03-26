import os
import platform
import typing as t
from pathlib import Path
from urllib.parse import urlencode
import zstandard as zstd
import json
from httpx_ws import connect_ws
from atproto import IdResolver


def event_stream(
    collections: t.Sequence[str] = tuple(),
    dids: t.Sequence[str] = tuple(),
    handles: t.Sequence[str] = tuple(),
    cursor: int | None = 0,
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
    query_enc = urlencode(query, safe=":.")
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
