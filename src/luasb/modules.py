import os
import httpx


modules = [
    'https://raw.githubusercontent.com/rxi/json.lua/master/json.lua',
    'https://raw.githubusercontent.com/philanc/plc/master/plc/base85.lua'
]

modules_dir: str = ""


def load_modules(basepath: str):
    global modules_dir
    modules_dir = basepath
    os.makedirs(basepath, exist_ok=True)
    for module in modules:
        path = os.path.basename(module)
        path = os.path.join(basepath, path)

        if os.path.exists(path):
            continue

        response = httpx.get(module)
        response.raise_for_status()

        with open(path, 'w') as f:
            f.write(response.text)
