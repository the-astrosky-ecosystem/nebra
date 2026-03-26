"""Subscribes to the NASA GCN Kafka stream and uses nebra to crosspost it onto
atprotocol.
"""

import os
from gcn_kafka import Consumer


client_id = os.getenv("GCN_CLIENT_ID", None)
client_secret = os.getenv("GCN_CLIENT_SECRET", None)


if client_id is None or client_secret is None:
    raise ValueError(
        "You must set the GCN_CLIENT_ID and GCN_CLIENT_SECRET env variables."
    )


# Connect as a consumer (client "tae-gcn")
# Warning: don't share the client secret with others.
consumer = Consumer(client_id=client_id, client_secret=client_secret)

# Subscribe to topics and receive alerts
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
        # "gcn.heartbeat",
    ]
)
while True:
    for message in consumer.consume(timeout=1):
        if message.error():
            print(message.error())
            continue
        # Print the topic and message ID
        print(f"topic={message.topic()}, offset={message.offset()}")
        value = message.value()
        print(value)
