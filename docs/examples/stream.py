"""
Streaming data with nebra
========================

This script demonstrates how to stream data from the AT Protocol Jetstream using nebra.
"""

import nebra


def handle_message(message: dict) -> None:
    """Custom message handler that prints the message and extracts key fields."""
    if "record" not in message:
        print("No record found")
        return

    record = message["record"]

    print(
        f"New matadisco record! It was published at {record.get('publishedAt', '???')}."
    )
    print(f"   tags    : {record.get('tags', None)}")
    print(f"   preview : {record.get('preview', None)}")
    print(f"   resource: {record.get('resource', None)}")


nebra.stream(collections=["cx.vmx.matadisco"], message_handler=handle_message)
