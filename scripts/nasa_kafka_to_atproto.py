"""Subscribes to the NASA GCN Kafka stream and uses nebra to crosspost it onto
atprotocol with robust error handling and automatic retries.
"""

import json
import os
import time
from typing import Generator, Dict, Any

from gcn_kafka import Consumer

from nebra import get_atproto_utc_time
from nebra.rebroadcast import RebroadcastClient

client_id = os.getenv("GCN_CLIENT_ID", None)
client_secret = os.getenv("GCN_CLIENT_SECRET", None)


if client_id is None or client_secret is None:
    raise ValueError(
        "You must set the GCN_CLIENT_ID and GCN_CLIENT_SECRET env variables."
    )


def _remove_large_fields(value):
    """Remove large fields from the event data to keep messages manageable."""
    if "healpix_file" in value:
        value.pop("healpix_file")
    if "event" in value and value["event"] is not None and "skymap" in value["event"]:
        value["event"].pop("skymap")
    if (
        "external_coinc" in value
        and value["external_coinc"] is not None
        and "combined_skymap" in value["external_coinc"]
    ):
        value["external_coinc"].pop("combined_skymap")


def gcn_event_generator() -> Generator[Dict[str, Any], None, None]:
    """Generator function that yields GCN events from the Kafka stream."""
    consumer = Consumer(client_id=client_id, client_secret=client_secret)
    consumer.subscribe(
        [
            "gcn.circulars",
            "gcn.notices.chime.frb",
            "gcn.notices.dsa110.frb",
            "gcn.notices.einstein_probe.wxt.alert",
            "gcn.notices.icecube.lvk_nu_track_search",
            "gcn.notices.icecube.gold_bronze_track_alerts",
            "igwn.gwalert",
            "gcn.notices.superk.sn_alert",
            "gcn.notices.swift.bat.guano",
            "gcn.heartbeat",
        ]
    )
    
    while True:
        for message in consumer.consume(timeout=1):
            if message.error():
                print(f"Message error: {message.error()}")
                continue

            if message.topic() == "gcn.heartbeat":
                print(f"\rLast heartbeat: {get_atproto_utc_time()}", end="")
                continue

            # Print the topic and message ID
            print(f"\nNew message! topic={message.topic()}, offset={message.offset()}")
            value = json.loads(message.value())

            # Process it
            print("Processing...")
            _remove_large_fields(value)
            
            # Create the event to yield
            event = {
                "$type": "eco.astrosky.transient.gcn",
                "topic": message.topic(),
                "eventID": message.offset(),
                "data": json.dumps(value),
                "createdAt": get_atproto_utc_time(),
            }
            
            yield event
            print("Yielded event for rebroadcast\n")


if __name__ == "__main__":
    # Start the rebroadcast client with our generator
    print("Starting NASA GCN Kafka to ATProto rebroadcast...")
    
    # Create and start the client
    client = RebroadcastClient(
        generator_factory=gcn_event_generator,
        max_retries=5,  # Maximum retry attempts for failed sends
        initial_retry_delay=1.0,  # Initial delay in seconds for retries
        max_queue_size=1000,  # Maximum size of the event queue
        reuse_session=True  # Pass through to the send function
    )
    
    # Start the client and handle keyboard interrupt for clean shutdown
    try:
        client.start()
        # Keep running until KeyboardInterrupt
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt, shutting down...")
        client.stop()
