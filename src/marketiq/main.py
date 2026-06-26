import asyncio
import logging
import sys

import uvicorn

from marketiq.api.app import create_app
from marketiq.config import get_settings


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    settings = get_settings()
    config = uvicorn.Config(
        create_app(), host=settings.api_host, port=settings.api_port
    )
    server = uvicorn.Server(config)
    asyncio.run(server.serve())
