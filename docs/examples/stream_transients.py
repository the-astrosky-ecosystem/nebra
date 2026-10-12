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
        "New transient detected!"
    )
    print(f"author={message.get('did', 'unknown')}")
    print(f"  time={record['time']}")
    print(f"    ra={record['ra']:.5f}")
    print(f"   dec={record['dec']:.5f}")
    print(f"  amag={record['mag']:.5f}")


nebra.stream(collections=["eco.astrosky.transient.example"], message_handler=handle_message)
