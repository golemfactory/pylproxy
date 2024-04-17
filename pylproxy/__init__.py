import os
import asyncio
import time
import aiohttp
from aiohttp import web
import socket
import logging

logger = logging.getLogger(__name__)


async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    pid = os.getpid()
    text = "{:.2f}: Hello {}! Process {} is treating you\n".format(time.time(), name, pid)

    # parse X-Server-Addr to get the server address
    server_addr = request.headers.get('X-Server-Addr', None)
    # parse X-Server-Port to get the server port
    server_port = request.headers.get('X-Server-Port', None)
    # parse X-Remote-Addr to get the remote address
    remote_addr = request.headers.get('X-Remote-Addr', None)
    logger.info(f"Server address: {server_addr}")
    logger.info(f"Server port: {server_port}")
    logger.info(f"Remote address: {remote_addr}")

    return web.Response(text=text)


class PylProxy:
    def __init__(self):
        pass

    def __repr__(self):
        return "PylProxy()"

    async def start(self, host, port):
        app = web.Application()
        app.router.add_route('GET', '/{tail:.*}', handle)

        runner = aiohttp.web.AppRunner(app)
        await runner.setup()
        self._site = aiohttp.web.TCPSite(runner, host, port)
        await self._site.start()

        logger.info(f"Server started at http://{host}:{port}")
