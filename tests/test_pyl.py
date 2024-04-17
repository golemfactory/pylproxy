import asyncio
import logging
import pylproxy

pytest_plugins = ("pytest_asyncio",)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_pyl():
    import pylproxy

    prox = pylproxy.PylProxy()
    proxy = await prox.start("0.0.0.0", 9990)
    await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(test_pyl())
