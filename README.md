[![PyPI](https://img.shields.io/badge/PyPI-package-blue.svg)](https://pypi.org/project/nebra/)


# nebra

Stream or send time-critical scientific data live and for free on the ATProtocol, with a simple, fast Python module.

> [!WARNING]  
> This package is in early development, and may have breaking changes in the near future. We do not (yet) recommend using it for production science.

Below is a minimal readme for the basic features of the package; more docs to come later!

## Installation

nebra is on PyPI; you can install it with

```bash
pip install nebra
```

## How to use

nebra can be used as a CLI (command line interface) tool or directly through Python.

### Streaming data

nebra can stream any type of record in real-time. This uses [jetstream](https://github.com/bluesky-social/jetstream), a lightweight add-on to data streaming on AT Protocol that allows you to filter by type of data, 

After installing nebra into your virtual environment, you can check out its data streaming with a command like

```bash
python -m nebra stream --collection=eco.astrosky.transient.* --handle=transient-xposter.astrosky.eco
```

which will output all transient-type records maintained by [The Astrosky Ecosystem](https://astrosky.eco/) and posted by our transient crossposting account, `transient-xposter.astrosky.eco`, to your console. You can view the kinds of records this will stream with a tool like [pdsls](https://pdsls.dev/at://did:plc:2o4hrvrj5vsicfuqlxhtk6qy).

Alternatively, you can use nebra within Python. The above command can be replicated with

```python
import nebra

nebra.stream(
    collections=["eco.astrosky.transient.*"], 
    handles=["transient-xposter.astrosky.eco"],
)
```

nebra can stream **any type of record** on the AT Protocol. For instance, viewing [Matadisco](https://matadisco.org/) open data records in real time is as easy as

```python
nebra.stream(collections=["cx.vmx.matadisco"])
```

More functionality, including cursor saving, error recovery, and callback functions will be added in due course.


### Sending data

Sending data is currently not possible with the CLI. Nevertheless, it's easy!

The main thing to make sure of is that your data conforms to the **schema** of the data you want to send. All data on ATProtocol obeys a lexicon definition. For instance, The Astrosky Ecosystem reposts NASA General Coordinates Network events on AT Protocol, for which we have a schema definition [`eco.astrosky.transient.gcn`](https://lexicon.garden/lexicon/did:plc:prqcuvros7du3jmyotr3iuap/eco.astrosky.transient.gcn/docs) [(view docs)](https://lexicon.garden/lexicon/did:plc:prqcuvros7du3jmyotr3iuap/eco.astrosky.transient.gcn/docs). Alternatively, publishing a Matadisco record would require conforming to the [`cx.vmx.matadisco`](https://lexicon.garden/lexicon/did:plc:3mdq56yhyqq5k6d4guztheaf/cx.vmx.matadisco/docs) schema [(view docs)](https://lexicon.garden/lexicon/did:plc:3mdq56yhyqq5k6d4guztheaf/cx.vmx.matadisco/docs).

Once you have an idea of the schema, you will need an AT Protocol account. The most common kind is just a [Bluesky](https://bsky.app) account, which you may already have. Set the following environment variables before running nebra:

- `NEBRA_HANDLE`: your account's handle. E.g.: `example.bsky.social`
- `NEBRA_PASSWORD`: an app password for your account. You may also use your real password (not recommended!)
- `NEBRA_BASE_URL` (optional): the base URL of your account. For accounts hosted on non-Bluesky servers, this will be the server address of your personal data server; for instance, Astrosky accounts would need to set this to `https://astrosky.social`.

Then, post the data using nebra with `nebra.send`. This function accepts a dictionary as argument and **will default to saving your session to a .session file** - make sure not to accidentally upload any session to e.g. GitHub. Your dictionary should contain a `$type` field that has the namespace of the schema that the record will follow.


```python
import nebra

nebra.send(record, reuse_session=True)
```

As a more complete example, posting a record that conforms with the `eco.astrosky.transient.gcn` schema could look like

```python
record = dict(
    "$type": "eco.astrosky.transient.gcn",
    "topic": "gcn.test",
    "eventID": 578245324,
    "data": "{"someData": "someValue"}",
    "createdAt": nebra.get_atproto_utc_time(),
)
nebra.send(record)
```

or a Matadisco record could be posted with

```python
record = dict(
    "$type": "cx.vmx.matadisco",
    "resource": "https://cdsarc.cds.unistra.fr/viz-bin/Cat?J/A+A/686/A42",
    "publishedAt": nebra.get_atproto_utc_time(),
)
nebra.send(record)
```

note that in both cases, we used the convenience function `nebra.get_atproto_utc_time()`, which provides a maximally ATProtocol-compatible timestamp (which is necessary for certain types of data).

More functionality, including better error feedback and validation will be added in due course. In addition, we are planning on adding an async version of the send function to allow for faster bulk item sending, and documentation on how to write and publish your own lexicons.


## Contributing

Contributions are highly welcome! You should follow [The Astrosky Ecosystem's style guide](https://github.com/the-astrosky-ecosystem/development-guide?tab=readme-ov-file#workflows-and-standards) with your pull request. Opening an issue first for discussion before writing a PR is usually wise.

## License

MIT license; see [here](https://github.com/the-astrosky-ecosystem/nebra/blob/main/LICENSE).
