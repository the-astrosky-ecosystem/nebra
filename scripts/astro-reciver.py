import nebra


def handle_message(message: dict) -> None:
    """Custom message handler that prints the message and extracts key fields."""
    if "record" not in message:
        print("No record found")
        return

    record = message["record"]
    
    print(f" astroColibriID={record['astroColibriID']}")
    print(f" alertType={record['alertType']}")
    print(f" broker={record['broker']}")
    print(f" createdAt={record['createdAt']}")
    print(f" observatory={record['observatory']}")
    print(f" triggerID={record['triggerID']}")
    print("--------------------------------------------------")


nebra.stream(collections=["science.astro-colibri.alert.ac"], message_handler=handle_message)