import click

from .broadcast import DataSource, RebroadcastClient
from .client import send
from .jetstream import stream
from .time import get_atproto_utc_time

__all__ = ["DataSource", "RebroadcastClient", "get_atproto_utc_time", "send", "stream"]


@click.group()
def cli():
    """Command-line interface for nebra.
    
    Returns
    -------
    click.Group
        A Click command group for the nebra CLI.
    """


# Add the `stream` command to the CLI group
cli.add_command(stream)


def main():
    """Entry point for the nebra CLI.
    
    This function is called when the `nebra` command is executed.
    It initializes and runs the Click command-line interface.
    """
    cli()
