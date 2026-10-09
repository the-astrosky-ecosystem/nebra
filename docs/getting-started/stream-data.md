# Stream data

For users, one of the most powerful things that `nebra` does is to allow you to easily stream data. This is possible in both plain Python and as a terminal command.


## In Python

Streaming data in Python with `nebra` is easy. By default, nebra will output events to the console. Let's stream all events on the Bluesky social network:


```python
import nebra

nebra.stream(collections=["app.bsky.feed.*"])
```

We can be more specific, and replace our wildcard with specific record types that we'd like:

```python
nebra.stream(collections=["app.bsky.feed.post"])
```

or restrict by handle:

```python
nebra.stream(collections=["app.bsky.feed.*"], handles=["emily.space", "astrosky.eco"])
```

By default, `nebra.stream` just writes events to the console. Instead, we can write a custom function that takes events as dictionaries and uses them as we'd like. For instance, this function will filter for gravitational waves posted by `transient-xposter.astrosky.eco` using the `eco.astrosky.transient.gcn` schema:

```python
def filter_gravitational_waves(event: dict):
    record = event.record
    if record.get("topic", "n/a") == "igwn.gwalert":
        print("A gravitational wave just happened!")
        do_some_cool_science(record)
    else:
        print("Event has wrong topic.")


nebra.stream(
    collections=["eco.astrosky.transient.gcn"],
    handles=["transient-xposter.astrosky.eco"],
    message_handler=filter_gravitational_waves
)
```

Check out [the full API](../api/stream.md) for more information.


## On the command line (CLI)

Streaming data with `nebra` is easy to play around with using the CLI interface. In CLI mode, each record is output on a single line as a JSON object. For instance: this command will stream **all records being created on Bluesky, live** (often 500+/second). Try running it for a few seconds and look at the output:

```bash
nebra stream --collections=app.bsky.feed.*
```

or, we could try streaming all matadisco records on the network (usually a few per 10 minutes):

```bash
nebra stream --collections=app.bsky.*
```

You can see a full list of options with

```bash
nebra stream --help
```

Common options are to filter records by account, such as by their AT Protocol handle / unique identifier (DID). These options can be a comma-separated list of account handles:

```bash
nebra stream --handles=emily.space,astrosky.eco
```


### A note on uvx

If you have [`uv`](https://docs.astral.sh/uv/) installed, you don't even need to install anything - `nebra` can be ran with `uv`'s tool runner, `uvx`. Prepend `uvx` to any of the above commands (e.g. `uvx nebra stream --collection=app.bsky.*`) and your command can run anywhere with `uv` installed.

