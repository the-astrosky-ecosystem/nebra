import os

from astrocolibri import Consumer

from nebra import DataSource, get_atproto_utc_time, rebroadcast

# from nebra.client import 

def astro_colibri_producer(data_source: DataSource, client_username: str, client_password: str):
    with Consumer(
        username=client_username,
        password=client_password,
    ) as consumer:
        print("consumer is good")
        consumer.subscribe(["astrocolibri.all.JSON"])
        print("subscribe is also good")
        # Runs until you stop it, waiting for the next alert.
        while data_source.is_active():
            for alert in consumer.consume():
                
                event = alert.value()
                print(f"New message about alert {event['astro_colibri_id']}")

                event_to_send = {
                    "$type": "science.astro-colibri.alert.ac",
                    "alertType": event["type"],
                    "astroColibriID": event["astro_colibri_id"],
                    "broker": "astrocolibri.all.JSON",
                    "createdAt": get_atproto_utc_time(),
                    "data": alert.json(),
                    "observatory": event["observatory"],
                    "triggerID": event["trigger_id"]
                }
                print(f"Sent event to AT Protocol: {event_to_send}")
                
                data_source.add_event(event_to_send)
                data_source.mark_producer_running()

def get_and_check_env_variables():
    client_id = os.getenv("ASTROCOLIBRI_USERNAME", None)
    client_secret = os.getenv("ASTROCOLIBRI_PASSWORD", None)

    if client_id is None or client_secret is None:
        raise RuntimeError(
            "You must set the ASTROCOLIBRI_USERNAME and ASTROCOLIBRI_PASSWORD environment "
            "variables to be able to subscribe to the Astro-COLIBRI stream."
        )

    # Also check the nebra login variables
    if (
        os.getenv("NEBRA_HANDLE", None) is None
        or os.getenv("NEBRA_PASSWORD", None) is None
    ):
        raise RuntimeError(
            "You must set the NEBRA_HANDLE and NEBRA_PASSWORD environment variables to "
            "the handle and app password (NOT your real password!) of the AT Protocol "
            "account that you wish to post records to."
        )

    return client_id, client_secret

if __name__ == "__main__":
    # Start the rebroadcast client
    print("Starting Astro-COLIBRI Kafka to ATProto rebroadcast...")

    # Get credentials from environment variables
    client_id, client_secret = get_and_check_env_variables()

    # Start rebroadcasting with the GCN producer
    rebroadcast(
        astro_colibri_producer,
        kwargs={"client_username": client_id, "client_password": client_secret},
    )