"""
Rebroadcasting data with nebra
=============================

This script demonstrates how to rebroadcast data from an event source onto the AT Protocol using nebra.

Prerequisites:
- Set the NEBRA_HANDLE environment variable to your AT Protocol handle (e.g., "your-handle.bsky.social").
- Set the NEBRA_PASSWORD environment variable to your app password.
- If you are on a non-Bluesky PDS, be sure to also set NEBRA_BASE_URL to the base URL of your PDS (e.g. https://eurosky.social)
"""

import random
import time

import nebra


def random_event_producer(data_source: nebra.DataSource) -> None:
    """A producer function that generates random astronomical events for demonstration purposes."""
    print("Starting random event producer...")
    event_id = 0

    while data_source.is_active():
        event_id += 1
        event = {
            "$type": "eco.astrosky.transient.example",
            "observatory": "ACMMAW-5",
            "time": nebra.get_atproto_utc_time(),
            "ra": random.uniform(0, 360),  # Random Right Ascension
            "dec": random.uniform(-90, 90),  # Random Declination
            "mag": random.uniform(10, 20),  # Random Magnitude
            "eventID": event_id,
        }

        print(f"Event {event_id}:")
        print(f"  time={event['time']}")
        print(f"    ra={event['ra']:.5f}")
        print(f"   dec={event['dec']:.5f}")
        print(f"  amag={event['mag']:.5f}")
        print("---------------------------")
        data_source.add_event(event)
        data_source.mark_producer_running()
        time.sleep(random.uniform(0.5, 3))


# Start rebroadcasting with our producer function
print("Starting rebroadcast client...")

nebra.rebroadcast(random_event_producer)
