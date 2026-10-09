#!/usr/bin/env python3
"""
Sending Data with Nebra
=======================

This script demonstrates how to send data using Nebra on the ATProtocol.

Prerequisites:
- Set the NEBRA_HANDLE environment variable to your ATProto handle (e.g., "your-handle.bsky.social").
- Set the NEBRA_PASSWORD environment variable to your app password.

Example:
    $ export NEBRA_HANDLE="your-handle.bsky.social"
    $ export NEBRA_PASSWORD="your-app-password"
    $ python sending.py
"""

import os
from nebra.client import send


def send_text_record():
    """Send a simple text record to the ATProtocol."""
    record = {
        "$type": "app.bsky.feed.post",
        "text": "Hello, ATProtocol! This is a test post sent using Nebra.",
        "createdAt": "2026-10-09T00:00:00Z"
    }
    print("Sending text record...")
    send(record)
    print("Text record sent successfully!")


def send_custom_record():
    """Send a custom record with floating-point data to the ATProtocol."""
    record = {
        "$type": "eco.astrosky.transient",
        "eventID": "test-event-123",
        "ra": 12.34,  # Right Ascension (floating-point)
        "dec": 56.78,  # Declination (floating-point)
        "mag": 18.5,  # Magnitude (floating-point)
        "createdAt": "2026-10-09T00:00:00Z"
    }
    print("Sending custom record with floating-point data...")
    send(record)
    print("Custom record sent successfully!")


if __name__ == "__main__":
    # Check if credentials are set
    if not os.getenv("NEBRA_HANDLE") or not os.getenv("NEBRA_PASSWORD"):
        print("Error: NEBRA_HANDLE and NEBRA_PASSWORD environment variables must be set.")
        print("Please set them before running this script.")
        exit(1)
    
    send_text_record()
    send_custom_record()