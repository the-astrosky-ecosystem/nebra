# Example script for rebroadcasting data with Nebra
"""
Rebroadcasting Data with Nebra
=============================

This script demonstrates how to rebroadcast data from an event source onto the ATProtocol using Nebra.

Prerequisites:
- Set the NEBRA_HANDLE environment variable to your ATProto handle (e.g., "your-handle.bsky.social").
- Set the NEBRA_PASSWORD environment variable to your app password.

Example:
    $ export NEBRA_HANDLE="your-handle.bsky.social"
    $ export NEBRA_PASSWORD="your-app-password"
    $ python rebroadcasting.py
"""

import os
import random
import time

import nebra


class RandomEventDataSource(nebra.DataSource):
    """A DataSource that generates random astronomical events for demonstration purposes."""

    def run(self) -> None:
        """Generate random events and add them to the queue."""
        print("Starting RandomEventDataSource...")
        event_id = 0

        while not self.stop_event.is_set():
            event_id += 1
            event = {
                "$type": "eco.astrosky.transient",
                "eventID": f"random-event-{event_id}",
                "ra": random.uniform(0, 360),  # Random Right Ascension
                "dec": random.uniform(-90, 90),  # Random Declination
                "mag": random.uniform(10, 20),  # Random Magnitude
                "createdAt": "2026-10-09T00:00:00Z"
            }

            if not self.add_event(event):
                print("Failed to add event to queue (queue full)")

            # Sleep for a random interval to simulate real-world event generation
            time.sleep(random.uniform(0.5, 2.0))


if __name__ == "__main__":
    # Check if credentials are set
    if not os.getenv("NEBRA_HANDLE") or not os.getenv("NEBRA_PASSWORD"):
        print("Error: NEBRA_HANDLE and NEBRA_PASSWORD environment variables must be set.")
        print("Please set them before running this script.")
        import sys
        sys.exit(1)

    # Create a data source and rebroadcast client
    print("Starting rebroadcast client...")
    print("Press Ctrl+C to stop.")
    
    data_source = RandomEventDataSource()
    nebra.rebroadcast(data_source)
