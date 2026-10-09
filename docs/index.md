# Nebra: Stream Scientific Data on the ATProtocol

Stream or send time-critical scientific data live and for free on the [ATProtocol](https://atproto.com/), with a simple, fast Python module.

`nebra` is a project by [The Astrosky Ecosystem](https://astrosky.eco/), originally built to help share astronomical data around the world more efficiently. 


## Why nebra?

Scientific data usually lives in many different places, and it is challenging to find a single, consistent source of data about a given topic. The AT Protocol can make this possible: at its core, it is a decentralized way to share JSON object-like data with others. This enables two exciting cases:

- If your data is already a JSON-like object (e.g. a Python dict): then you can send it around the world with `nebra`, with about five minutes of setup.
- If your data is large or not JSON-like: you could post metadata that points to your data store using a metadata schema like [Matadisco](https://matadisco.org/), which can allow for things like [live previews of ESA satellite feeds](https://vmx.github.io/matadisco-viewer/).

Likewise, if you're a user interested in data stream(s) that other people are already posting, then `nebra` makes it incredibly easy to subscribe to them.


## Why the AT Protocol?

By posting data on the AT Protocol, **anyone** can view it and index it **immediately** - making it a fantastic choice for data you might want to share, make an app from, or more. `nebra` could power your next citizen science project, embedded on a device; it could be a way to share time-critical notifications with other scientists; or it could just be a better way to share data in your field.


## Getting Started
1. [Install `nebra`](installation.md)
2. Check out the [Examples](examples/) to learn how to send, stream, or rebroadcast data with functional Python scripts.
3. Explore the [API Reference](api/core.md) for detailed documentation.

## License

`nebra` is licensed under the MIT License.
