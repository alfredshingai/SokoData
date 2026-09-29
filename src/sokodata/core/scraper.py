"""Base scraper with queue-based retries."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from sokodata.core.queue import Task, complete, dequeue, enqueue, fail
from sokodata.datasets.markets.store import connect as db_connect

log = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for scrapers with queue-based retry logic."""

    def __init__(self, db_path: str, task_type: str, max_attempts: int = 3):
        self.db_path = db_path
        self.task_type = task_type
        self.max_attempts = max_attempts

    @abstractmethod
    def execute(self, payload: dict) -> dict:
        """Execute the scrape task. Return result dict."""
        pass

    def enqueue(self, payload: dict, priority: int = 0) -> str:
        """Add a scrape job to the queue."""
        return enqueue(self.db_path, self.task_type, payload, max_attempts=self.max_attempts)

    def run_worker(self, limit: int = 10) -> int:
        """Process pending tasks. Returns number of tasks processed."""
        from sokodata.core.queue import Task, complete, dequeue, fail
        from sokodata.datasets.markets.store import connect

        tasks = dequeue(self.db_path, limit=limit)
        processed = 0
        for task in tasks:
            try:
                result = self.execute(task.payload)
                complete(self.db_path, task.id, result)
                processed += 1
            except Exception as e:
                fail(self.db_path, task.id, str(e))
        return processed

    def process_all(self, batch_size: int = 10) -> int:
        """Process all pending tasks in batches."""
        total = 0
        while True:
            processed = self.run_worker(limit=10)
            if processed == 0:
                break
            total += processed
        return total