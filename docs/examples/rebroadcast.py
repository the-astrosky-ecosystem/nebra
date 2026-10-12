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


class RandomEventDataSource(nebra.DataSource):
    """A DataSource that generates random astronomical events for demonstration purposes."""

    def run(self) -> None:
        """Generate random events and add them to the queue."""
        print("Starting RandomEventDataSource...")
        event_id = 0

        while not self.stop_event.is_set():
            event_id += 1
            event = {
                "$type": "eco.astrosky.transient.example",
                "observatory": "ACMMAW-5",
                "time": nebra.get_atproto_utc_time(),
                "ra": random.uniform(0, 360),  # Random Right Ascension
                "dec": random.uniform(-90, 90),  # Random Declination
                "mag": random.uniform(10, 20),  # Random Magnitude
            }
            
            print("New event:")
            print(f"  time={event['time']}")
            print(f"    ra={event['ra']:.5f}")
            print(f"   dec={event['dec']:.5f}")
            print(f"  amag={event['mag']:.5f}")
            self.add_event(event)
            time.sleep(random.uniform(0.5, 3))


# Create a data source and rebroadcast client
print("Starting rebroadcast client...")

data_source = RandomEventDataSource()
nebra.rebroadcast(data_source)
