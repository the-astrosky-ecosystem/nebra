"""Subscribes to the NASA GCN Kafka stream and uses nebra to crosspost it onto
atprotocol.
"""

import os
import json
from gcn_kafka import Consumer
from nebra import send, get_atproto_utc_time


client_id = os.getenv("GCN_CLIENT_ID", None)
client_secret = os.getenv("GCN_CLIENT_SECRET", None)


if client_id is None or client_secret is None:
    raise ValueError(
        "You must set the GCN_CLIENT_ID and GCN_CLIENT_SECRET env variables."
    )

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


def _remove_large_fields(value):
    if "healpix_file" in value:
        value.pop("healpix_file")
    if "event" in value:
        if "skymap" in value["event"]:
            value["event"].pop("skymap")
    if "external_coinc" in value:
        if value["external_coinc"] is not None:
            if "combined_skymap" in value["external_coinc"]:
                value["external_coinc"].pop("combined_skymap")


def _send_gcn_event(message, value):
    event = {
        "$type": "eco.astrosky.transient.gcn",
        "topic": message.topic(),
        "eventID": message.offset(),
        "data": json.dumps(value),
        "createdAt": get_atproto_utc_time(),
    }
    send(event)


def _write_to_file(message, value):
    with open("test_file", "a") as file:
        file.write(
            f"-----------------------\ntopic={message.topic()}, offset={message.offset()}\n"
            + json.dumps(value, indent=2)
        )


while True:
    for message in consumer.consume(timeout=1):
        if message.error():
            print(message.error())
            continue

        if message.topic() == "gcn.heartbeat":
            print(f"\rLast heartbeat: {get_atproto_utc_time()}", end="")

        else:
            # Print the topic and message ID
            print(f"\nNew message! topic={message.topic()}, offset={message.offset()}")
            value = json.loads(message.value())

            # Process it
            print("Sending...")
            _remove_large_fields(value)
            _send_gcn_event(message, value)
            _write_to_file(message, value)

            print("Done!\n")
