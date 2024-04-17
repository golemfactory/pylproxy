import logging

pytest_plugins = ("pytest_asyncio",)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_pylproxyimport():
    import pylproxy

    prox = pylproxy.PylProxy()
    logger.info(prox)
    assert prox
