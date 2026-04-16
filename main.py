from copy import deepcopy
import re
import os
import logging
import asyncio
from scrapy.selector import Selector
from dotenv import load_dotenv

from utils.helpers import extract_pid_from_url
from utils.http_requests import Request
from utils.stocks_resolver import get_resolver
from constants import FORMAT_LOGINING, PRODUCT_NAME_XPATH, PRODUCT_CURRENT_PRICE_XPATH, \
    PRODUCT_PRICE_BEFORE_DISCOUNT_XPATH, PRODUCT_IMAGES_XPATH, PRODUCT_COLORS_XPATH, PRODUCT_SIZES_XPATH, \
    PRODUCT_SELECTED_COLOR_XPATH, START_URLS, QUICKVIEW_URL, MAKE_REQUEST_MESSAGE, SUCCESS_REQUEST_MESSAGE, \
    FAIL_REQUEST_MESSAGE, QUICKVIEW_COLOR_URL

load_dotenv()

logging.basicConfig(level=logging.INFO, format=FORMAT_LOGINING)
logger = logging.getLogger(__name__)


class JoesNewBalanceOutletParser:

    def get_identifiers(self, style_code, size_val, size_label, product_url):
        shop_sku = f"{style_code}_{size_val}"
        return {
            'shop_sku': shop_sku,
            'color_group_id': style_code,
            'url': product_url,
        }

    def get_origin_name(self, response):
        name = response.xpath(PRODUCT_NAME_XPATH).get('')
        return {'origin_name': name.strip()}

    def get_brand(self):
        return {'brand': 'New Balance'}

    def get_prices(self, response):
        price = response.xpath(PRODUCT_CURRENT_PRICE_XPATH).get('0')
        price_before_discount = response.xpath(
            PRODUCT_PRICE_BEFORE_DISCOUNT_XPATH).get()
        return {
            'price': price,
            'price_before_discount': price_before_discount,
        }

    def get_images(self, response):
        images = []
        for src in response.xpath(PRODUCT_IMAGES_XPATH).getall():
            if src.startswith('http') and 'scene7' in src:
                clean = re.sub(r'\?.*', '', src)
                if clean not in images:
                    images.append(clean)
        main_photo = images[0] if images else None
        additional = ','.join(images[1:]) if len(images) > 1 else None
        return {
            'main_photo': main_photo,
            'additional_photos': additional,
        }

    def get_colors(self, response):
        colors = []
        for btn in response.xpath(PRODUCT_COLORS_XPATH):
            colors.append({
                'style_code': btn.attrib.get('data-attrvalue', ''),
                'color_name': btn.attrib.get('data-variation-value', ''),
                'selected': 'selected' in btn.attrib.get('class', ''),
                'variant_id': btn.attrib.get('data-variantid', ''),
            })
        return colors

    def get_current_style(self, response):
        colors = self.get_colors(response)
        current_style = ''
        for c in colors:
            if c['selected']:
                current_style = c['style_code']
                break
        return current_style

    def get_sizes(self, response):
        sizes = []
        for btn in response.xpath(PRODUCT_SIZES_XPATH):
            label = btn.attrib.get('aria-label', '')
            size_match = re.search(r'\(([\d.]+)\)', label)
            size_val = size_match.group(1) if size_match else ''
            size_label = label.replace('Select Size ', '').split('(')[0].strip()
            cls = btn.attrib.get('class', '')
            selectable = 'selectable' in cls
            unselectable = 'unselectable' in cls
            sizes.append({
                'size': size_val,
                'label': size_label,
                'in_stock': 5 if (selectable and not unselectable) else 0,
            })
        return sizes

    def get_selected_color_name(self, response):
        for btn in response.xpath(PRODUCT_SELECTED_COLOR_XPATH):
            if 'selected' in btn.attrib.get('class', ''):
                return btn.attrib.get('data-variation-value', '')
        return ''


class RunScraper(JoesNewBalanceOutletParser):
    def __init__(self):
        self.name = 'joesnewbalanceoutlet.com'
        self.client = Request()
        self.products_urls = []
        self.products_result = []
        self.visited_urls = []
        self.semaphore = asyncio.Semaphore(10)
        self.debug = bool(os.getenv("DEBUG"))
        self.source = "joesnewbalanceoutlet.com"
        self.resolver = get_resolver(source=self.source, currency="USD", debug=self.debug)

    async def run_stocks_mode(self):
        """STOCKS mode (get products urls from DB)"""
        self.resolver.open()
        self.products_urls = START_URLS
        tasks = []
        for url in self.products_urls:
            if url not in self.visited_urls:
                pid = extract_pid_from_url(url)
                product_url = QUICKVIEW_URL.format(pid=pid)
                self.visited_urls.append(product_url)
                tasks.append(
                    self.run_with_semaphore(
                        self.make_get_request,
                        url=product_url,
                        callback=self.parse_product,
                        kwargs={'url': url, 'pid': pid},
                        log_label="[run_stocks_mode]",
                    )
                )
        await asyncio.gather(*tasks)
        self.resolver.close()
        logger.info(f'Completed: {len(self.products_urls)} URLs | '
                    f'Results: {len(self.products_result)} variants | '
                    f'Requests: {self.client.count_requests} | '
                    f'Failed: {self.client.failed_requests}')

    async def make_get_request(self, url, callback, kwargs=None, log_label=""):
        kwargs = kwargs or {}
        logger.info(MAKE_REQUEST_MESSAGE.format(log_label=log_label, url=url))
        response = await self.client.scrape_page(url)
        if response:
            logger.info(SUCCESS_REQUEST_MESSAGE.format(log_label=log_label, url=url))
            html_text = response.get("response")
            await callback(html_text, kwargs=kwargs)
        else:
            logger.error(FAIL_REQUEST_MESSAGE.format(log_label=log_label, url=url))

    async def run_with_semaphore(self, coro_func, *args, **kwargs):
        async with self.semaphore:
            return await coro_func(*args, **kwargs)

    async def parse_product(self, html, **kwargs):
        """Сбор всех цветов товара"""
        kw = kwargs.get('kwargs', kwargs)
        original_url = kw.get('url', '')
        pid = kw.get('pid', '')

        response = Selector(text=html)
        colors = self.get_colors(response)

        if not colors:
            await self.parse_color_variant(html, original_url=original_url, pid=pid)
            return

        for color in colors:
            if color['selected']:
                await self.parse_color_variant(html, original_url=original_url, pid=pid)
            else:
                color_url = QUICKVIEW_COLOR_URL.format(pid=pid, style=color['style_code'])
                resp = await self.client.scrape_page(color_url)
                if resp:
                    await self.parse_color_variant(
                        resp.get("response"), original_url=original_url, pid=pid
                    )
                else:
                    logger.error(f"Failed to fetch color variant: {color['style_code']} for {pid}")

    async def parse_color_variant(self, html, original_url, pid):
        """Сбор всех размеров по одному цвету"""
        try:
            response = Selector(text=html)

            result = {}
            result.update(self.get_origin_name(response))
            result.update(self.get_brand())
            result.update(self.get_prices(response))
            result.update(self.get_images(response))
            result['origin_color'] = self.get_selected_color_name(response)

            sizes = self.get_sizes(response)
            current_style = self.get_current_style(response)

            for size in sizes:
                result_variant = deepcopy(result)
                result_variant.update(
                    self.get_identifiers(
                        style_code=current_style,
                        size_val=size['size'],
                        size_label=size['label'],
                        product_url=original_url,
                    )
                )
                result_variant['in_stock'] = size['in_stock']
                result_variant['size'] = size['label']

                if result_variant not in self.products_result:
                    self.resolver.process(result_variant)
                    self.products_result.append(result_variant)
                    logger.info(f"Yield result: {result_variant}")

        except Exception as e:
            logger.error(f"[parse_color_variant] Exception: {e} | URL: {original_url}")


async def main():
    await RunScraper().run_stocks_mode()

asyncio.run(main())
