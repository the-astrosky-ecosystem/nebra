import click

from .broadcast import DataSource, rebroadcast
from .client import send
from .jetstream import stream, stream_command
from .time import get_atproto_utc_time

__all__ = ["DataSource", "get_atproto_utc_time", "rebroadcast", "send", "stream"]


@click.group()
def cli():
    """Command-line interface for nebra."""


# Add the `stream` command to the CLI group
cli.add_command(stream_command)


def main():
    """Entry point for the nebra CLI.
    
    This function is called when the `nebra` command is executed.
    It initializes and runs the Click command-line interface.
    """
    cli()
