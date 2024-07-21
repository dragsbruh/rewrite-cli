import click

from rflow import rf
from rflow._exceptions import AuthenticationError, ConflictError
from utils import readable_time

from rich.console import Console
console = Console()
print = console.print

@click.group()
def auth(): pass


@auth.command()
@click.argument('token', type=str)
def login(token: str):
    print("Logging in...")
    try:
        me = rf.authenticate(token)
    except AuthenticationError:
        print("Invalid authentication token")
        return
    print("Login success")
    print(f"Welcome, {me.username}!")


@auth.command()
@click.option('--username', prompt="Choose a username")
@click.option('--email', prompt="Enter your email address")
def register(username: str, email: str):
    print(f"Registering as {username}")
    try:
        rf.register(username, email)
    except ConflictError as e:
        print(e.message)
        return

    print("An email was sent to the provided email address with access token to your account")
    print("Use the login command to login")


@auth.command()
def me():
    print("Retrieving user information...")
    try:
        me = rf.me()
    except AuthenticationError:
        print("Not authenticated")
        return
    print(f"Logged in as: {me.username}")
    print(f"User ID: {me.id}")
    console.print(f"Created at: {readable_time(me.created_at)}")


def confirm_action(prompt: str = "Do you want to continue?"):
    return click.confirm(prompt, default=False)


@auth.command()
def logout():
    if not confirm_action("Do you want to log out?"):
        return
    rf.logout()
    print("Logged out successfully")
