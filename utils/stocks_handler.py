from pathlib import Path
from datetime import datetime

import os
import logging
from dotenv import load_dotenv
from typing import List, Dict, Any
import json

load_dotenv()

logger = logging.getLogger()


class StocksHandler:
    """
        Handler для режима stocks.
    Если debug=True:
        - пишет NDJSON-файл в {cwd}/{source_name}-stocks.json
    """
    def __init__(self, source_name: str, currency: str, debug=False):
        self.debug = bool(debug)
        self.batch_size = 10 if self.debug else 1000
        self.source_name = source_name
        self.currency = currency
        self.buffer: List[Dict[str, Any]] = []

        if self.debug:
            storage_dir = Path(os.getcwd())
            storage_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            self.debug_file = storage_dir / f"{self.source_name.replace('.', '_').replace('/', '_')}-stocks-{timestamp}.json"

    def process(self, item: Dict[str, Any]):
        self.buffer.append(item)
        if len(self.buffer) >= self.batch_size:
            self._flush()

    def _flush(self):
        """Отправляет и/или сохраняет текущую партию, затем очищает буфер."""
        if not self.buffer:
            return
        batch = self.buffer.copy()
        self.buffer = []
        self._dump_to_file(batch)

    def _dump_to_file(self, batch):
        """Записывает buffer в NDJSON-файл (каждый объект в новой строке)."""
        if not batch:
            return

        os.makedirs(self.debug_file.parent, exist_ok=True)
        # Открываем в append режиме и записываем каждую запись как отдельную JSON-строку
        with self.debug_file.open("a", encoding="utf-8") as fh:
            for obj in batch:
                fh.write(json.dumps(obj, ensure_ascii=False) + "\n")

        logger.info("Wrote %d stock records to %s", len(batch), str(self.debug_file))

    def close(self):
        """При закрытии шлём остаток и/или сохраняем в файл."""
        self._flush()
        logger.info(f"[{self.source_name}] Flushed remaining products to file/API.")
