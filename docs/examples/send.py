"""
Sending data with nebra
=======================

This script demonstrates how to send data using nebra on the AT Protocol.

Prerequisites:
- Set the NEBRA_HANDLE environment variable to your AT Protocol handle (e.g., "your-handle.bsky.social").
- Set the NEBRA_PASSWORD environment variable to your app password.
"""

import nebra

record = {
    "$type": "app.bsky.feed.post",
    "text": "Hello, AT Protocol! This is a test post sent using nebra.",
    "createdAt": nebra.get_atproto_utc_time(),
}
print("Sending text record...")
nebra.send(record)
print("Text record sent successfully!")
