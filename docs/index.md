# Nebra: stream scientific data on the AT Protocol

Stream or send time-critical scientific data live and for free on the [AT Protocol](https://atproto.com/), with a simple, fast Python module.

`nebra` is a project by [The Astrosky Ecosystem](https://astrosky.eco/), originally built to help share astronomical data around the world more efficiently. 


<div style="font-size: 17px; border: 1px solid white; border-radius: 20px; padding: 20px; margin-bottom: 20px; margin-top: 30px"><p style="margin: 0px"><strong>⚠️ nebra is alpha software ⚠️</strong><br>nebra is under active development; the API may change and there may be bugs.</p></div>


## Why nebra?

Scientific data usually lives in many different places, and it is challenging to find a single, consistent source of data about a given topic. The AT Protocol can make this possible: at its core, it is a decentralized way to share JSON object-like data with others. This enables two exciting cases:

- If your data is already a JSON-like object (e.g. a Python dict): then you can send it around the world with `nebra`, with almost no setup required.
- If your data is large or not JSON-like: you could post metadata that points to your data store using a metadata schema like [Matadisco](https://matadisco.org/), which can allow for things like [live previews of ESA satellite feeds](https://vmx.github.io/matadisco-viewer/).

Likewise, if you're a user interested in data stream(s) that other people are already posting, then `nebra` makes it incredibly easy to subscribe to them.


## Why the AT Protocol?

By posting data on the AT Protocol, **anyone** can view it and index it **immediately** - making it a fantastic choice for data you might want to share, make an app from, or more. `nebra` could power your next citizen science project, embedded on a device; it could be a way to share time-critical notifications with other scientists; or it could just be a better way to share data in your field.


## Getting started
1. [Install `nebra`](getting-started/installation.md)
2. Check out how to [stream data](getting-started/stream-data.md) or [send data](getting-started/send-data.md) to learn how to send, stream, or rebroadcast data with functional Python snippets.
3. Explore the [API Reference](api/stream.md) for detailed documentation.

## License

`nebra` is licensed under [an MIT License](https://github.com/the-astrosky-ecosystem/nebra/blob/main/LICENSE).
