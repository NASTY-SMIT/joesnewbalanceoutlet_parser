import logging
from random import choice
from asyncio import sleep
from random import uniform

from rnet import Client, Proxy, Impersonate
from constants import PROXIES, HEADERS

logger = logging.getLogger(__name__)

PROXY_OBJECTS = [
    Proxy.all(url, username=user, password=pwd)
    for url, user, pwd in PROXIES
]


class Request:
    def __init__(self):
        self.max_attempts = 10
        self.count_requests = 0
        self.failed_requests = 0

    async def scrape_page(self, url, cb_kwargs=None):
        response = await self.fetch_page(url, cb_kwargs)
        return response

    async def fetch_page(self, url, cb_kwargs=None):
        for attempt in range(self.max_attempts):
            self.count_requests += 1
            proxy = choice(PROXY_OBJECTS)
            await sleep(uniform(0.1, 0.3))

            client = Client(verify=False, impersonate=Impersonate.Chrome131)
            try:
                resp = await client.get(url, headers=HEADERS, proxy=proxy)

                if resp.status == 200:
                    text = await resp.text()
                    if len(text) > 1000:
                        return {"response": text, "kwargs": cb_kwargs}
                    else:
                        logger.warning(f"Small response ({len(text)}b), likely challenge | URL: {url}")
                elif resp.status == 429:
                    logger.warning(f"429 Rate limited | URL: {url} | sleeping 5s")
                    await sleep(5)
                elif resp.status == 403:
                    logger.warning(f"403 Blocked | URL: {url} | attempt {attempt + 1}")
                    await sleep(1)
                else:
                    logger.error(f"Status {resp.status} | URL: {url}")

            except Exception as e:
                logger.error(f"Request error: {e} | URL: {url}")
                await sleep(1)
                continue

        self.failed_requests += 1
        logger.error(f"Failed to fetch {url} after {self.max_attempts} attempts")
        return None
