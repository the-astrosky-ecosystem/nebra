"""Subscribes to the NASA GCN Kafka stream and uses nebra to crosspost it onto
atprotocol with robust error handling and automatic retries.
"""

import json
import os
import time

from gcn_kafka import Consumer

from nebra import get_atproto_utc_time
from nebra.broadcast import DataSource, rebroadcast


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


def get_consumer(
    client_id: str, client_secret: str, topics: list | None = None
) -> Consumer:
    """Create and configure a GCN Kafka consumer.

    Parameters
    ----------
    client_id : str
        GCN Kafka client ID.
    client_secret : str
        GCN Kafka client secret.
    topics : list, optional
        List of topics to subscribe to. If None, uses default topics.

    Returns
    -------
    Consumer
        Configured GCN Kafka consumer.
    """
    consumer = Consumer(client_id=client_id, client_secret=client_secret)

    # Use provided topics or default topics
    topics_to_subscribe = (
        topics
        if topics is not None
        else [
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

    consumer.subscribe(topics_to_subscribe)
    return consumer


def gcn_producer(
    data_source: DataSource,
    client_id: str,
    client_secret: str,
    topics: list | None = None,
) -> None:
    """Run the GCN event producer, handling its own error recovery.

    Parameters
    ----------
    data_source : DataSource
        The data source to add events to.
    client_id : str
        GCN Kafka client ID.
    client_secret : str
        GCN Kafka client secret.
    topics : list, optional
        List of topics to subscribe to. If None, uses default topics.
    """
    print(f"Starting GCN producer for topics: {topics or 'default topics'}")
    consumer = get_consumer(client_id, client_secret, topics)

    while data_source.is_active():
        try:
            messages = consumer.consume(timeout=1)

        except Exception as e:  # noqa
            print(f"Error in GCN data source: {e}")

            # Wait before retrying
            time.sleep(5)

            # Reset consumer
            consumer = get_consumer(client_id, client_secret, topics)
            continue

        for message in messages:
            if message.error():
                print(f"Message error: {message.error()}")
                continue

            if message.topic() == "gcn.heartbeat":
                print(f"\rLast heartbeat: {get_atproto_utc_time()}", end="")
                data_source.mark_producer_running()
                continue

            # Fetch the message
            print(f"\nNew message! topic={message.topic()}, offset={message.offset()}")
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

            data_source.add_event(event)
            print("Added event to queue\n")


if __name__ == "__main__":
    # Start the rebroadcast client
    print("Starting NASA GCN Kafka to ATProto rebroadcast...")

    # Get credentials from environment variables
    client_id = os.getenv("GCN_CLIENT_ID")
    client_secret = os.getenv("GCN_CLIENT_SECRET")

    if client_id is None or client_secret is None:
        raise ValueError(
            "You must set the GCN_CLIENT_ID and GCN_CLIENT_SECRET env variables."
        )

    # Start rebroadcasting with the GCN producer
    rebroadcast(
        gcn_producer, kwargs={"client_id": client_id, "client_secret": client_secret}
    )
