import os
import lupa  # type: ignore
import json

from lupa import LuaRuntime  # type: ignore
from typing import Any, Optional

from . import modules as lmods
from ._exceptions import LuaRuntimeError


default_allowed_modules = []
default_blocked_globals = []

variable = dict[str, Any] | str | bytes

_default_max_memory = 50 * 1024 * 1024  # 50mb


class LuaSandbox:
    def __init__(
        self,
        values: Optional[dict[str, variable]] = None,
        max_memory: int = _default_max_memory,
        allowed_modules: list[str] = default_allowed_modules,
        blocked_globals: list[str] = default_blocked_globals
    ) -> None:
        self.modules_path = f'{lmods.modules_dir}/?.lua'
        self.allowed_modules = allowed_modules
        self.blocked_globals = blocked_globals

        self.allowed_modules.extend(
            [os.path.splitext(x)[0] for x in os.listdir(lmods.modules_dir)])

        self.runtime = LuaRuntime(
            unpack_returned_tuples=True,
            max_memory=max_memory,
            attribute_filter=self._filter_attr_access
        )

        self.set_globals()
        if values:
            self.inject_values(values)

    def set_globals(self):
        self._old_require = self.runtime.globals().require
        
        self.runtime.execute(
            f"package.path = '{self.modules_path};'")

        for item in self.blocked_globals:
            code = f'{item} = nil'
            self.runtime.execute(code)

        self.lua_globals = self.runtime.globals()

        self.lua_globals.Result = {}
        self.Result = {}
        self.output = []
        self.lua_globals.print = self._print
        self.lua_globals.require = self._require


    def inject_values(self, values: dict[str, variable]):
        self.runtime.execute('json = require("json")')
        self.runtime.execute('base85 = require("base85")')

        for name, value in values.items():
            if isinstance(value, str) or isinstance(value, bytes):
                self.lua_globals[name] = value
            else:
                code = f'{name} = json.decode([[{json.dumps(value)}]]);'
                self.runtime.execute(code)

        self.lua_globals.json = None
        self.lua_globals.base85 = None

    def execute(self, code: str):
        try:
            self.runtime.execute(code)
        except Exception as e:
            raise LuaRuntimeError(f'Error executing script: {e}')

        try:
            self.Result = self._lua_table_to_dict(self.lua_globals.Result)
        except Exception as e:
            raise LuaRuntimeError(f'Error parsing result')

    def _require(self, modname: str):
        if modname in self.allowed_modules:
            return self._old_require(modname)
        raise LuaRuntimeError(f'Cannot import {modname}')

    def _filter_attr_access(self, _: object, attr: str, __: bool):
        if attr.startswith('_'):
            raise LuaRuntimeError(f'Cannot access or modify attribute {attr}')

    def _lua_table_to_dict(self, table: Any) -> dict[str, Any]:
        if not table:
            return {}

        python_dict: dict[str, Any] = {}
        for key, value in table.items():
            if lupa.lua_type(value) == 'table':
                python_dict[key] = self._lua_table_to_dict(value)
            else:
                python_dict[key] = value

        return python_dict

    def _print(*args):
        pass
