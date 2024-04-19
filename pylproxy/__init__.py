import aiohttp
from aiohttp import web
import logging
from typing import Mapping

logger = logging.getLogger(__name__)

CALLER_HEADER = "X-Caller"
CALLEE_HEADER = "X-Callee"

YAGNA_REST_PORT = 6000
HOST_REST_PORT_START = 6001
HOST_REST_PORT_END = 6010

class PylProxy:
    def __init__(
        self, node_names: Mapping[str, str], ports: Mapping[str, Mapping[int, int]]
    ):
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
        self._logger.info(
            f"PylProxy created with _port_to_name: {self._port_to_name}, _name_to_port: {self._name_to_port}"
        )

    def __repr__(self):
        return "PylProxy()"

    async def handle(self, request: aiohttp.web_request.Request):

        # parse X-Server-Addr to get the server address
        server_addr = request.headers.get("X-Server-Addr", None)
        # parse X-Server-Port to get the server port
        try:
            server_port = int(request.headers.get("X-Server-Port", None))
        except ValueError:
            return web.Response(status=400, text=f"Invalid server port: {server_port}")

        # parse X-Remote-Addr to get the remote address
        remote_addr = request.headers.get("X-Remote-Addr", None)
        self._logger.debug(f"Server address: {server_addr}")
        self._logger.debug(f"Server port: {server_port}")
        self._logger.debug(f"Remote address: {remote_addr}")

        try:
            agent_node = self._node_names[remote_addr]
        except KeyError:
            return web.Response(status=400, text=f"Remote addr: {remote_addr} not found in mapping")

        extra_headers = {}
        protocol = "http"
        if server_port == YAGNA_REST_PORT:
            # This should be a request from an agent running in a yagna container
            # calling that container's daemon. We route this request to that
            # container's host-mapped daemon port.
            host = "127.0.0.1"
            port = self._name_to_port[agent_node]
            extra_headers[CALLER_HEADER] = f"{agent_node}:agent"
            extra_headers[CALLEE_HEADER] = f"{agent_node}:daemon"

        elif HOST_REST_PORT_START <= server_port <= HOST_REST_PORT_END:
            # This should be a request from an agent running on the Docker host
            # calling a yagna daemon in a container. We use localhost as the address
            # together with the original port, since each daemon has its API port
            # mapped to a port on the host chosen from the specified range.
            host = "127.0.0.1"
            port = server_port
            extra_headers[CALLER_HEADER] = f"{agent_node}:agent"
            try:
                daemon_node = self._port_to_name[server_port]
            except KeyError:
                return web.Response(status=400, text=f"Server port {server_port} not found in mapping")
            extra_headers[CALLEE_HEADER] = f"{daemon_node}:daemon"
        else:
            return web.Response(status=400, text="Invalid server port")

        async with aiohttp.ClientSession() as session:
            if request.has_body:
                body = await request.read()
            else:
                body = None
            self._logger.info(
                "forwarding request {}, headers: {} - data: {}".format(request, request.headers, body)
            )

            target_url = f"{protocol}://{host}:{port}{request.raw_path}"
            req = session.request(
                request.method,
                target_url,
                headers=request.headers,
                data=body,
            )
            try:
                async with req as resp:
                    response = web.Response(
                        headers=resp.headers, status=resp.status, body=await resp.read()
                    )
                    self._logger.info(f"Request from {extra_headers[CALLER_HEADER]} "
                                      f"for {server_addr}:{server_port}{request.raw_path} "
                                      f"routed to {extra_headers[CALLEE_HEADER]} at {host}:{port}")
                    if self._callback_response:
                        self._callback_response(request_no, response)
                    return response
            except aiohttp.ClientConnectionError as e:
                return web.Response(status=400, text=f"Client connection error: {e} when calling: {target_url}")

        # req.headers[CALLEE_HEADER] = f"{remote_addr}:daemon"

        # agent_node = self._node_names[remote_addr]

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

        return web.Response(status=400, text="NOT OK")

    async def start(self, host, port, callback_request=None, callback_response=None):
        app = web.Application()
        app.router.add_route("GET", "/{tail:.*}", lambda request: self.handle(request))
        app.router.add_route("PUT", "/{tail:.*}", lambda request: self.handle(request))
        app.router.add_route("POST", "/{tail:.*}", lambda request: self.handle(request))
        app.router.add_route(
            "DELETE", "/{tail:.*}", lambda request: self.handle(request)
        )
        self._callback_request = callback_request
        self._callback_response = callback_response

        self._runner = aiohttp.web.AppRunner(app)
        await self._runner.setup()
        self._site = aiohttp.web.TCPSite(self._runner, host, port)
        await self._site.start()

        self._logger.info(f"Server started at http://{host}:{port}")

    async def stop(self):
        self._logger.info("Server stopping...")
        await self._site.stop()
        await self._runner.shutdown()
        self._logger.info("Server stopped")
