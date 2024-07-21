import os
from pathlib import Path
from typing import Any
import click

import httpx
from rich.console import Console
from rich.table import Table
import toml

from rflow import rf
from utils import readable_time

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
    lmods = rf.get_lua_config()['modules']

    for mod in lmods:
        name = os.path.basename(mod)
        response = httpx.get(mod)

        try:
            response.raise_for_status()
        except httpx.HTTPError:
            print(f"Failed to download module '{name}'")
            exit(1)

        (path / "lua_modules" / f"{name}.lua").write_bytes(response.content)


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
