import os
import sqlite3
import logging
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, Any, Optional

from utils.stocks_handler import StocksHandler

load_dotenv()

logger = logging.getLogger()


class LocalProductsDB:
    def __init__(self, source: str):
        self.source = source.replace('.', '_').replace('/', '_')
        db_env = os.getenv("DB_DATA_PATH")
        if db_env: self.db_path = Path(db_env)
        else: self.db_path = None

    def open_db(self):
        """ Открываем локальную БД парсера, которая содержит в себе
        все данные с выгрузки. Далее она будет использоваться для получения данных по SKU
        -> sqlite3.Connection | None """
        target_file = f"{self.source}.db"

        # если задан путь — ищем только там
        search_dirs = [self.db_path] if self.db_path else [os.getcwd()]

        for directory in search_dirs:
            if not directory:  continue
            for root, _, files in os.walk(directory):
                if target_file in files:
                    try:
                        conn = sqlite3.connect(os.path.join(root, target_file))
                        logger.info(f"Local database opened: {target_file}")
                        return conn
                    except sqlite3.Error as e:
                        logger.error(f"Error when opening: {target_file} - {e}")
                        return None

        logger.error(f"File {target_file} not found")
        return None

    def get_urls(self, skus: set[str] = None):
        """ Получаем уникальные ссылки и список отсутствующих SKU
        Ссылки будут использоваться для парсингов стоков, а отсутствующие SKU для вывода в лог
        -> list[dict] """

        conn = self.open_db()
        if not conn: return [], skus if skus else set()

        unique_products = []  # массив с уникальными продуктами
        seen_urls = set()  # ссылки, которые уже сохранили в unique_products
        count_duplicates = 0  # количество дублей от вариаций, которые не сохраняли, но взяли url

        cursor = conn.cursor()
        cursor.execute("SELECT newmen_sku, url FROM products")

        while True:
            rows = cursor.fetchmany(10000)
            if not rows: break
            for sku, link in rows:
                if not skus or sku in skus:  # skus = None (debug mode) & sku in ozon skus
                    if link:
                        clean_url = link.split("?")[0]
                        if clean_url not in seen_urls:
                            unique_products.append({'url': clean_url, 'sku': sku})
                            seen_urls.add(clean_url)
                        else:
                            count_duplicates += 1

        logger.info(f'We have added a url to the product data for - {len(unique_products) + count_duplicates} SKUs')

        conn.close()
        return unique_products

class OzonDB:
    def __init__(self, source: str):
        self.source = source.replace('.', '_').replace('/', '_')
        db_env = os.getenv("OZON_DB_PATH")
        if db_env: self.base_path = Path(db_env)
        else: self.base_path = None

    def search_dbs(self) -> list[Path]:
        """ Проходимся по каждому магазину OZON из папки results
        Выполняем поиск нужных .db по названию source, забираем путь до базы данных """

        if not self.base_path.exists():
            logger.error(f"Folder {self.base_path} not found")
            return []

        return [p for p in self.base_path.rglob("*.db") if p.stem == self.source]

    def get_unique_skus(self, db_paths: list[Path]) -> set[str]:
        """ Открываем каждую .db и забираем уникальные SKU
        по которым необходимо получить url из локальной базы и обновить стоки
        -> set(str) """

        unique_skus = set()
        for db_path in db_paths:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT sku FROM products")
            while True:
                rows = cursor.fetchmany(10000)
                if not rows: break
                for (sku,) in rows:
                    unique_skus.add(sku)

            conn.close()

        logger.info(f'Number of SKUs received from OZON to update stocks: {len(unique_skus)}')
        return unique_skus


class StockProducts:
    """Работа с товарами для стоков"""
    def __init__(self, source: str, currency: str, batch_size: int = 1000, debug: bool = False):
        self.debug = debug
        self.local_db = LocalProductsDB(source)
        self.ozon_db = OzonDB(source)
        self.source = source
        self.currency = currency
        self.batch_size = batch_size
        self.handler: Optional[StocksHandler] = None

    def open(self):
        self.handler = StocksHandler(source_name=self.source, currency=self.currency, debug=self.debug)

    def process(self, item: Dict[str, Any]):
        if not self.handler:
            raise RuntimeError("Handler not opened")
        self.handler.process(item)

    def close(self):
        if self.handler:
            self.handler.close()


def get_resolver(source: str, currency: str, debug: bool = False) -> StockProducts:
    """Фабрика для выбора обработчика"""
    return StockProducts(source=source, currency=currency, debug=debug)