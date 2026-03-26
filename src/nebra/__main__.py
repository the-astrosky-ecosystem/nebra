from .jetstream import stream
from .client import send
import click


@click.group()
def cli():
    pass


if __name__ == "__main__":
    # stream_events(collections=["eco.astrosky.transient.*"])
    # one_day_ago = int((time() - 24 * 60**2) * 1e6)
    # stream_events(cursor=one_day_ago, handles=["emily.space"])
    # stream_events(cursor=None, handles=["emily.space"])
    cli.add_command(stream)
    # cli.add_command(send)

    cli()
