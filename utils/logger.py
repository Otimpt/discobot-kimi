"""
Configuração de Logging
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_dir: str = "data/logs"
):
    """Configura o sistema de logging."""
    
    # Criar diretório de logs
    if log_to_file:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        log_file = Path(log_dir) / f"bot_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Configurar formato
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Handler de console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configurar logger raiz
    root_logger = logging.getLogger("discord-bot")
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    if log_to_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Reduzir logs de bibliotecas
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
