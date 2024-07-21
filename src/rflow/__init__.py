import os
import toml
import httpx

from typing import Any, Optional

from rflow._exceptions import AuthenticationError, BadRequestError, NotFoundError
from ._models import User, Flow, PublicFlow


class RewriteFlow:
    client: httpx.Client
    _auth: str | None
    conf_path: str = os.path.expanduser('~/.rfconf.toml')

    def __init__(self, api_base_url: str) -> None:
        self.client = httpx.Client()
        self.client.base_url = api_base_url
        self._auth = None

        self.load_config()

    def load_config(self):
        if not os.path.exists(self.conf_path):
            return
        with open(self.conf_path, 'r') as f:
            config = toml.load(f)

        if 'auth' in config:
            self._auth = f"{config['auth']}"
            self.client.headers['Authorization'] = config['auth']

    def dump_config(self):
        config_data: dict[str, Any] = {}
        if self._auth:
            config_data['auth'] = self._auth

        with open(self.conf_path, 'w') as f:
            toml.dump(config_data, f)

    def me(self):
        response = self._request('get', '/auth/me')
        return User.model_validate(response.json())

    def register(self, username: str, email: str):
        response = self._request('post', '/auth/register', json={
            'username': username,
            'email': email
        })
        return User.model_validate(response.json())

    def authenticate(self, token: str):
        self._auth = f"{token}"
        self.client.headers['Authorization'] = self._auth

        try:
            me = self.me()
        except AuthenticationError as e:
            self._auth = None
            del self.client.headers['Authorization']

            raise e

        self.dump_config()
        return me

    def logout(self):
        self._auth = None
        del self.client.headers['Authorization']
        self.dump_config()

    def get_flow(self, flow_id: str):
        response = self._request('get', f'/flows/flow/{flow_id}')
        return PublicFlow.model_validate(response.json())

    def get_my_flow(self, flow_id: str):
        response = self._request('get', f'/flows/my/{flow_id}')
        return Flow.model_validate(response.json())

    def get_my_flows(self):
        response = self._request('get', f'/flows/list')
        return [Flow.model_validate(f) for f in response.json()]

    def get_my_code(self, flow_id: str):
        response = self._request('get', f'/flows/my/{flow_id}/code')
        return response.json()

    def update_flow(self, flow: Flow):
        self._request('patch', f'/flows/update_info/{flow.id}', json={
            'env': flow.env.copy(),
            'name': flow.name
        })

    def set_my_code(self, flow_id: str, code: str):
        self._request('patch', f'/flows/update',
                      json={'id': flow_id, 'code': code})

    def create_flow(self, name: str, env: dict[str, str], code: str):
        data = {'name': name, 'env': env, 'code': code}
        response = self._request('post', '/flows/new', json=data)
        return Flow.model_validate(response.json())

    def get_lua_config(self):
        response = self._request('get', '/misc/lua_config')
        return response.json()

    def get_hook_url(self, flow_id: str):
        return f"{self.client.base_url}/flows/call/{flow_id}"

    def _request(self, method: str, url: str, json: Optional[dict[str, Any]] = None):
        response = self.client.request(method, url, json=json)
        if response.status_code == 401:
            data = response.json()
            if 'detail' in data:
                raise AuthenticationError(data['detail'])
            raise AuthenticationError(
                f'Unauthorized error when requesting {url} with {method}')
        elif response.status_code == 400:
            data = response.json()
            if 'detail' in data:
                raise BadRequestError(data['detail'])
            raise BadRequestError(
                f'Bad request error when requesting {url} with {method}: {data}')
        elif response.status_code == 404:
            data = response.json()
            if 'detail' in data:
                raise NotFoundError(data['detail'])
            raise NotFoundError(
                f'Not found error when requesting {url} with {method}: {data}')
        response.raise_for_status()
        return response


rf = RewriteFlow('http://localhost')
