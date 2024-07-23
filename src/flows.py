import os
import re
import toml
import httpx
import click

from pathlib import Path
from typing import Any

import luasb
from luasb._exceptions import LuaRuntimeError
from rflow import rf
from luasb.sandbox import LuaSandbox, variable
from rich.table import Table
from rich.console import Console
from rflow._exceptions import AuthenticationError, NotFoundError

from utils import get_readme, get_rewrite_helper_code, readable_time

console = Console()
print = console.print


def scaffold_flow_directory(target_path: str, name: str):
    path = Path(target_path)
    path.mkdir(parents=True, exist_ok=True)

    config: dict[str, Any] = {
        'name': name,
        'env': {}
    }

    template_script = """print("Hello, World!")"""

    (path / "rflow.config.toml").write_text(toml.dumps(config))
    (path / "main.lua").write_text(template_script)

    (path / "lua_modules").mkdir(exist_ok=True, parents=True)

    print("Getting module list...")
    lmods = rf.get_lua_config()['modules']

    (path / "README.md").write_text(get_readme())

    for mod in lmods:
        name = os.path.basename(mod)
        print(f"\tFetching module {os.path.splitext(name)[0]}...")
        response = httpx.get(mod)

        try:
            response.raise_for_status()
        except httpx.HTTPError:
            print(f"Failed to download module '{name}'")
            exit(1)

        (path / "lua_modules" / f"{name}").write_bytes(response.content)

    print("Fetching helper module")
    (path / "rewrite.lua").write_text(get_rewrite_helper_code())


@click.group()
def flows(): pass


@flows.command()
def show():
    console = Console()
    table = Table(title="Your flows")

    table.add_column('ID')
    table.add_column('Name')
    table.add_column('Created At')
    table.add_column('Analytics')

    flows = rf.get_my_flows()
    for flow in flows:
        table.add_row(flow.id, flow.name, readable_time(
            flow.created_at), str(flow.analytics))

    console.print(table)


@flows.command()
def create():
    name = click.prompt("Flow name")
    path = click.prompt("Directory to create flow in")

    scaffold_flow_directory(path, name)
    print(f"Flow '{name}' created successfully at '{path}'")


env_value_pattern = re.compile(r'^[\w\s\-\/:.@,=+_(){};\'"]+$')
env_key_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


@flows.command()
def publish():
    req_paths = ['rflow.config.toml', 'main.lua']
    if not all([os.path.exists(p) for p in req_paths]):
        print("One or two required files missing: ", ', '.join(req_paths))
        print("Are you sure you are in the correct directory?")
        exit(1)

    with open('rflow.config.toml', 'r') as f:
        fconf = toml.load(f)

    try:
        name = fconf['name']
        renv: dict[Any, Any] = fconf['env'] if 'env' in fconf else {}
        id = fconf['_rf']['id'] if '_rf' in fconf else None

        if type(renv) != dict:
            raise ValueError('renv')

    except KeyError as e:
        print(
            f"rflow.config.toml is missing required key (or) incorrect type: '{e}'")
        exit(1)
    except ValueError as e:
        print(f"rflow.config.toml is having wrong value: '{e}'")
        exit(1)

    with open('main.lua', 'r') as f:
        code = f.read()

    print(f"Publishing flow {name}...")
    env: dict[str, str] = {}
    for name, value in renv.items():
        if len(value) > 2048:
            print(
                f"Invalid environment variable: {name}. Value is too long, max is 2048 characters.")
            exit(1)
        if len(name) > 100:
            print(
                f"Invalid environment variable: {name}. Name is too long, max is 100 characters.")
            exit(1)
        if not name.strip() or not value.strip():
            print(
                f"Invalid environment variable: {name}. Name or value is empty.")
            exit(1)

        if not env_key_pattern.match(name):
            print(
                f"Invalid environment variable: {name}. Name contains invalid characters.")
            exit(1)
        if not env_value_pattern.match(str(value)):
            print(
                f"Invalid environment variable: {name}. Value contains invalid characters.")
            exit(1)

        if type(value) != str:
            print(
                f"WARNING: Invalid type for environment variable: {name}. Value must be a string")
        env[name] = str(value)
    if id:
        try:
            flow = rf.get_my_flow(id)
        except NotFoundError:
            print(f"Flow '{id}' not found.")
            exit(1)

        print("Updating environment and code...")
        flow.env = env
        flow.name = name
        rf.update_flow(flow)
        rf.set_my_code(id, code)
    else:
        print("Creating flow...")
        flow = rf.create_flow(name, env, code)

        fconf['_rf'] = {
            'id': flow.id
        }

        with open('rflow.config.toml', 'w') as f:
            toml.dump(fconf, f)

    print("Done!")


@flows.command()
@click.option('-i', '--id')
def pull(id: str):
    try:
        flow = rf.get_my_flow(id)
    except NotFoundError:
        print(f"Flow '{id}' not found.")
        exit(1)
    except AuthenticationError:
        print("Authentication error. Please make sure you are logged in.")
        exit(1)

    scaffold_flow_directory(".", "loading...")
    print(f"Pulling code for flow '{flow.name}'...")
    code = rf.get_my_code(id)

    with open('main.lua', 'w') as f:
        f.write(code)

    fconf: dict[str, Any] = {}

    fconf['name'] = flow.name
    fconf['env'] = flow.env

    fconf['_rf'] = {
        'id': id
    }

    with open('rflow.config.toml', 'w') as f:
        toml.dump(fconf, f)

    print("Done!")


@flows.command()
def test():
    print("Starting sandbox...")
    luasb.modules.modules_dir = 'lua_modules'

    req_paths = ['rflow.config.toml', 'main.lua']

    if not all([os.path.exists(p) for p in req_paths]):
        print("One or two required files missing: ", ', '.join(req_paths))
        print("Are you sure you are in the correct directory?")
        exit(1)

    with open('rflow.config.toml', 'r') as f:
        fconf = toml.load(f)
    with open('main.lua', 'r') as f:
        code = f.read()

    try:
        renv: dict[Any, Any] = fconf['env'] if 'env' in fconf else {}

        if type(renv) != dict:
            raise ValueError('renv')

    except KeyError as e:
        print(
            f"rflow.config.toml is missing required key (or) incorrect type: '{e}'")
        exit(1)
    except ValueError as e:
        print(f"rflow.config.toml is having wrong value: '{e}'")
        exit(1)

    if os.path.exists('payload.toml'):
        with open('payload.toml', 'r') as f:
            rpayload = toml.load(f)

        payload: dict[str, variable] = {}

        payload['body'] = rpayload['body'] if 'body' in rpayload else {}
        payload['headers'] = rpayload['headers'] if 'headers' in rpayload else {}
        payload['params'] = rpayload['params'] if 'params' in rpayload else {}
        payload['env'] = renv
    else:
        payload = {}
        payload['body'] = {}
        payload['headers'] = {}
        payload['params'] = {}
        payload['env'] = renv

    sb = LuaSandbox(payload, print_fn=print)
    try:
        sb.execute(code)
    except LuaRuntimeError as e:
        print(f"Lua runtime error occurred: {e}")
        exit(1)


@flows.command()
@click.option('-i', '--id')
def url(id: str):
    print(rf.get_hook_url(id))
