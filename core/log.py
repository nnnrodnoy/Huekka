import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Настраивает систему логирования"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)
    logger.addHandler(console_handler)
    
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "userbot.log"),
        maxBytes=5*1024*1024,
        backupCount=3
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    httpx_logger = logging.getLogger("httpx")
    httpx_logger.setLevel(logging.WARNING)
    
    return logger