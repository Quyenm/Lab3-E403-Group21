import logging
import json
import os
from datetime import datetime
from typing import Any, Dict

class IndustryLogger:
    def __init__(self, name: str = "AI-Lab-Agent", log_dir: str = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Tránh duplicate handler khi chạy lại cell trong Jupyter
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Luôn lưu log cạnh file logger.py, không phụ thuộc working directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir  = log_dir or os.path.join(base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
        print(f"[Logger] Lưu log tại: {log_file}")  # để confirm

        file_handler    = logging.FileHandler(log_file, encoding="utf-8")
        console_handler = logging.StreamHandler()

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log_event(self, event_type: str, data: Dict[str, Any]):
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "data": data
        }
        self.logger.info(json.dumps(payload, ensure_ascii=False))

    def info(self, msg: str):
        self.logger.info(msg)

    def error(self, msg: str, exc_info: bool = True):
        self.logger.error(msg, exc_info=exc_info)

logger = IndustryLogger()