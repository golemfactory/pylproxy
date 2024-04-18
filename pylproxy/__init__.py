import os
import asyncio
import time
import aiohttp
from aiohttp import web
import socket
import logging
from typing import Mapping

logger = logging.getLogger(__name__)

CALLER_HEADER = "X-Caller"
CALLEE_HEADER = "X-Callee"

YAGNA_REST_PORT = 6000


class PylProxy:
    def __init__(self, node_names: Mapping[str, str], ports: Mapping[str, Mapping[int, int]]):
        self._logger = logger
        self._logger.info(f"Creating PylProxy: {node_names}, {ports}")
        self._node_names = node_names
        self._name_to_port = {}
        self._port_to_name = {}
        for node, port_mapping in ports.items():
            if YAGNA_REST_PORT in port_mapping:
                host_port = port_mapping[YAGNA_REST_PORT]
                name = node_names[node]
                self._name_to_port[name] = host_port
                assert host_port not in self._port_to_name
                self._port_to_name[host_port] = name
        self._logger.info(f"PylProxy created with _port_to_name: {self._port_to_name}, _name_to_port: {self._name_to_port}")

    def __repr__(self):
        return "PylProxy()"

    async def handle(self, request: aiohttp.web_request.Request):
        print(type(request))
        name = request.match_info.get('name', "Anonymous")
        pid = os.getpid()
        text = "{:.2f}: Hello {}! Process {} is treating you\n".format(time.time(), name, pid)

        self._logger.debug("incoming request {}, headers: {}".format(request, request.headers))

        # parse X-Server-Addr to get the server address
        server_addr = request.headers.get('X-Server-Addr', None)
        # parse X-Server-Port to get the server port
        server_port = request.headers.get('X-Server-Port', None)
        # parse X-Remote-Addr to get the remote address
        remote_addr = request.headers.get('X-Remote-Addr', None)
        self._logger.info(f"Server address: {server_addr}")
        self._logger.info(f"Server port: {server_port}")
        self._logger.info(f"Remote address: {remote_addr}")


        async with aiohttp.ClientSession() as session:
            if request.has_body:
                body = await request.read()
            else:
                body = None
            req = session.request(request.method,
                                  "http://127.0.0.1:6001" + request.raw_path,
                                  headers=request.headers,
                                  data=body)
            async with req as resp:
                return web.Response(headers=resp.headers, status=resp.status, body=await resp.read())
        #req.headers[CALLEE_HEADER] = f"{remote_addr}:daemon"

        #agent_node = self._node_names[remote_addr]

        if 0:
            self._logger.debug(
                "Request from %s for %s:%d/%s routed to %s at %s:%d",
                # request caller:
                req.headers[CALLER_HEADER],
                # original host, port and path:
                server_addr,
                server_port,
                req.path,
                # request recipient:
                req.headers[CALLEE_HEADER],
                # rewritten host and port:
                req.host,
                req.port,
            )

        return web.Response(text=text)


    async def start(self, host, port):
        app = web.Application()
        app.router.add_route('GET', '/{tail:.*}', lambda request: self.handle(request))
        app.router.add_route('PUT', '/{tail:.*}', lambda request: self.handle(request))
        app.router.add_route('POST', '/{tail:.*}', lambda request: self.handle(request))
        app.router.add_route('DELETE', '/{tail:.*}', lambda request: self.handle(request))

        runner = aiohttp.web.AppRunner(app)
        await runner.setup()
        self._site = aiohttp.web.TCPSite(runner, host, port)
        await self._site.start()

        self._logger.info(f"Server started at http://{host}:{port}")
