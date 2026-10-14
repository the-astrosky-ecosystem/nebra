"""
Streaming data with nebra
========================

This script demonstrates how to stream data from the AT Protocol Jetstream using nebra.
"""

from atproto import IdResolver

import nebra

resolver = IdResolver()


def handle_message(message: dict) -> None:
    """Custom message handler that prints the message and extracts key fields."""
    if "record" not in message:
        print("No record found")
        return

    record = message["record"]

    did = message.get("did", None)
    handle = None
    if did is not None:
        did_doc = resolver.did.resolve(did)
        if did_doc is not None:
            handle = did_doc.get_handle()

    print(f"Received event {record.get('eventID', '(no ID)')}")
    print(f"author={handle}")
    print(f"  time={record['time']}")
    print(f"    ra={record['ra']:.5f}")
    print(f"   dec={record['dec']:.5f}")
    print(f"  amag={record['mag']:.5f}")
    print("---------------------------")


nebra.stream(
    collections=["eco.astrosky.transient.example"], message_handler=handle_message
)
