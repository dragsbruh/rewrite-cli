import click

__version__ = "0.1.0"

from auth import auth
from flows import flows

@click.group()
def cli(): pass


cli.add_command(auth)
cli.add_command(flows)

if __name__ == "__main__":
    cli()
