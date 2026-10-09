#!/usr/bin/env python3
"""
Streaming Data with Nebra
========================

This script demonstrates how to stream data from the ATProtocol Jetstream using Nebra.

Example:
    $ python streaming.py --collection "eco.astrosky.transient"
"""

import json
import time
import typing as t
import click
from nebra.jetstream import run_stream


def handle_message(message: str) -> None:
    """Custom message handler that prints the message and extracts key fields."""
    try:
        data = json.loads(message)
        if "commit" in data and "ops" in data["commit"]:
            for op in data["commit"]["ops"]:
                if op["action"] == "create":
                    record = op["record"]
                    print(f"New record in collection {op['path']}:")
                    print(f"  Event ID: {record.get('eventID', 'N/A')}")
                    print(f"  RA: {record.get('ra', 'N/A')}")
                    print(f"  Dec: {record.get('dec', 'N/A')}")
                    print(f"  Mag: {record.get('mag', 'N/A')}")
                    print("---")
    except json.JSONDecodeError:
        print(f"Received non-JSON message: {message}")


@click.command()
@click.option(
    "--collection",
    "-c",
    multiple=True,
    help="The collections to subscribe to. If not provided, subscribe to all.",
    type=str,
    default=["eco.astrosky.transient"],
)
@click.option(
    "--handle",
    "-h",
    multiple=True,
    help="The ATProto handles to subscribe to. If not provided, subscribe to all.",
    type=str,
    default=[],
)
@click.option(
    "--cursor",
    "-u",
    help="The cursor to start from. If not provided or set to zero, start from 'now'.",
    type=int,
    default=0,
)
@click.option(
    "--duration",
    "-d",
    help="Duration in seconds to run the stream before exiting. If not provided, run indefinitely.",
    type=int,
    default=0,
)
def stream(collections: t.Sequence[str], handles: t.Sequence[str], cursor: int, duration: int):
    """Stream data from the ATProtocol Jetstream."""
    print(f"Starting stream for collections: {collections}")
    print(f"Handles: {handles}")
    print(f"Cursor: {cursor}")
    
    if duration > 0:
        print(f"Stream will run for {duration} seconds.")
        
        def run_with_timeout():
            run_stream(
                collections=collections,
                handles=handles,
                cursor=cursor,
                message_handler=handle_message,
            )
        
        # Run the stream in a separate thread to handle the timeout
        import threading
        stream_thread = threading.Thread(target=run_with_timeout, daemon=True)
        stream_thread.start()
        
        # Wait for the specified duration
        time.sleep(duration)
        print(f"Stream stopped after {duration} seconds.")
    else:
        print("Stream will run indefinitely. Press Ctrl+C to stop.")
        run_stream(
            collections=collections,
            handles=handles,
            cursor=cursor,
            message_handler=handle_message,
        )


if __name__ == "__main__":
    stream()