import os
import json
from dotenv import load_dotenv

load_dotenv()

proxies_raw = os.getenv("PROXIES_JSON")

START_URLS = [
            'https://www.joesnewbalanceoutlet.com/pd/nb-numeric-brandon-westgate-508/NM508V1-49306.html',
            'https://www.joesnewbalanceoutlet.com/pd/509/U509EV1-FTW-805505.html',
            'https://www.joesnewbalanceoutlet.com/pd/fresh-foam-x-860v13/M860V13-39163-PMG-NA.html',
            'https://www.joesnewbalanceoutlet.com/pd/fuelcell-supercomp-elite-v5/WRCELV5-50686.html',
            'https://www.joesnewbalanceoutlet.com/pd/530/MR530-32265-PMG-NA.html',
            'https://www.joesnewbalanceoutlet.com/pd/fresh-foam-bb-v3/BBFRSV3-48320.html',
            'https://www.joesnewbalanceoutlet.com/pd/wrpd-runner/UWRPDV1-49902.html',
            'https://www.joesnewbalanceoutlet.com/pd/made-in-uk-allerdale-vegetable-tanned-nubuck/UADWV1-49770.html',
            'https://www.joesnewbalanceoutlet.com/pd/1000d/M1000DV1-52155.html',
            'https://www.joesnewbalanceoutlet.com/pd/550/BB550V1-51942.html',
            'https://www.joesnewbalanceoutlet.com/pd/furon-elite-tf-v8/SF1TV8-50235.html',
        ]

MAKE_REQUEST_MESSAGE = "{log_label} MAKE REQUEST FOR URL  {url}"
SUCCESS_REQUEST_MESSAGE = "{log_label} SUCCESS REQUEST FOR URL  {url}"
FAIL_REQUEST_MESSAGE = "{log_label} Failed with get product - {url}"
FORMAT_LOGINING = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

DOMAIN = 'https://www.joesnewbalanceoutlet.com'

QUICKVIEW_URL = (
    'https://www.joesnewbalanceoutlet.com/on/demandware.store/'
    'Sites-JNBO-Site/en_US/Product-ShowQuickView?pid={pid}'
)

QUICKVIEW_COLOR_URL = (
    'https://www.joesnewbalanceoutlet.com/on/demandware.store/'
    'Sites-JNBO-Site/en_US/Product-ShowQuickView?dwvar_{pid}_style={style}&pid={pid}'
)


# XPATH ТОВАРОВ
PRODUCT_NAME_XPATH = '//h1[contains(@class, "product-name")]/text()'
PRODUCT_CURRENT_PRICE_XPATH = "//span[@class='price-value']//span[contains(@class, 'sales font-body-large ')]/span//@content"
PRODUCT_PRICE_BEFORE_DISCOUNT_XPATH = '//span[contains(@class, "strike-through")]//span[@class="value"]/@content'
PRODUCT_IMAGES_XPATH = '//div[contains(@class, "carousel-item")]//img/@src'
PRODUCT_COLORS_XPATH = '//button[@data-attr="style-value"]'
PRODUCT_SIZES_XPATH = '//button[@data-attr="size-value"]'
PRODUCT_SELECTED_COLOR_XPATH = '//button[@data-attr="style-value"]'

try:
    proxies_list = json.loads(proxies_raw)
except Exception as e:
    raise ValueError(f"Ошибка парсинга PROXIES_JSON: {e}\nПроверь формат в .env") from e

PROXIES = [
    (item["url"], item.get("user"), item.get("pass"))
    for item in proxies_list
    if item.get("url") and item.get("user") and item.get("pass")
]

HEADERS = {
    'X-Requested-With': 'XMLHttpRequest',
    'Accept': '*/*',
}
