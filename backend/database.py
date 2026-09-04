import asyncio
import os
from typing import Dict

from motor.motor_asyncio import AsyncIOMotorClient

from backend.config import get_settings

_database_clients: Dict[str, AsyncIOMotorClient] = {}


def _database_client_key() -> str:
    try:
        loop = asyncio.get_running_loop()
        return f"loop:{id(loop)}"
    except RuntimeError:
        return "default"


def get_database():
    settings = get_settings()
    mongo_url = settings["mongo_url"]
    db_name = settings["db_name"]

    if not mongo_url or not db_name:
        return None

    client_key = _database_client_key()
    client = _database_clients.get(client_key)
    if client is None:
        client = AsyncIOMotorClient(mongo_url)
        _database_clients[client_key] = client

    return client[db_name]


def close_database_connection() -> None:
    global _database_clients
    for client in list(_database_clients.values()):
        client.close()
    _database_clients = {}
