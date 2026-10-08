"""Subscribes to the NASA GCN Kafka stream and uses nebra to crosspost it onto
atprotocol with robust error handling and automatic retries.
"""

import json
import os
import time

from gcn_kafka import Consumer

from nebra import get_atproto_utc_time
from nebra.rebroadcast import DataSource, RebroadcastClient


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


class GCNDataSource(DataSource):
    """DataSource implementation for NASA GCN Kafka stream."""

    def __init__(self, max_queue_size: int = 1000):
        super().__init__(max_queue_size=max_queue_size)
        self.client_id = os.getenv("GCN_CLIENT_ID", None)
        self.client_secret = os.getenv("GCN_CLIENT_SECRET", None)

        if self.client_id is None or self.client_secret is None:
            raise ValueError(
                "You must set the GCN_CLIENT_ID and GCN_CLIENT_SECRET env variables."
            )

    def get_consumer(self) -> Consumer:
        """Create and configure a GCN Kafka consumer."""
        consumer = Consumer(client_id=self.client_id, client_secret=self.client_secret)
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
        return consumer

    def run(self) -> None:
        """Run the event source, handling its own error recovery."""
        consumer = self.get_consumer()

        while not self.stop_event.is_set():
            try:
                messages = consumer.consume(timeout=1)

            except Exception as e:  # noqa
                print(f"Error in GCN data source: {e}")

                # Wait before retrying
                time.sleep(5)

                # Reset consumer
                consumer = self.get_consumer()
                continue

            for message in messages:
                if message.error():
                    print(f"Message error: {message.error()}")
                    continue

                if message.topic() == "gcn.heartbeat":
                    print(f"\rLast heartbeat: {get_atproto_utc_time()}", end="")
                    continue

                # Fetch the message
                print(
                    f"\nNew message! topic={message.topic()}, offset={message.offset()}"
                )
                value = json.loads(message.value())
                _remove_large_fields(value)

                # Create & add the event
                event = {
                    "$type": "eco.astrosky.transient.gcn",
                    "topic": message.topic(),
                    "eventID": message.offset(),
                    "data": json.dumps(value),
                    "createdAt": get_atproto_utc_time(),
                }

                self.add_event(event)
                print("Added event to queue\n")


if __name__ == "__main__":
    # Start the rebroadcast client with our data source
    print("Starting NASA GCN Kafka to ATProto rebroadcast...")

    # Create the data source and client
    data_source = GCNDataSource(max_queue_size=1000)
    client = RebroadcastClient(data_source=data_source)

    # Start the client and handle keyboard interrupt for clean shutdown
    try:
        client.start()
        # Keep running until KeyboardInterrupt
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt, shutting down...")
        client.stop()
