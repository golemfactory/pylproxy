import asyncio
import logging
import pylproxy

pytest_plugins = ("pytest_asyncio",)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_pyl():
    names = {
        "172.19.0.8": "requestor",
        "172.19.0.9": "provider-1",
        "172.19.0.10": "provider-2",
        "172.19.0.1": "docker-host",
    }
    ports = {
        "172.19.0.8": {6000: 6004},
        "172.19.0.9": {6000: 6005},
        "172.19.0.10": {6000: 6006},
    }

    prox = pylproxy.PylProxy(names, ports)
    _ = await prox.start("0.0.0.0", 9990)
    await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(test_pyl())
