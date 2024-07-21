from pydantic import BaseModel


class FlowAnalytics(BaseModel):
    calls: int
    success: int
    failure: int

class Flow(BaseModel):
    id: str
    name: str
    author: str
    created_at: int
    last_modified: int
    analytics: FlowAnalytics
    env: dict[str, str]


class PublicFlow(BaseModel):
    id: str
    name: str
    author: str
    created_at: int


class User(BaseModel):
    id: str
    username: str
    created_at: int
