#!/usr/bin/env python3
"""
🤖 Discord AI Bot v2 - Versão Completa e Modular
Um bot de Discord avançado com múltiplos modos, memória inteligente,
suporte a Assistants API, geração de imagens e muito mais.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import Config
from core.bot_instance import BotInstance
from database.manager import DatabaseManager
from utils.logger import setup_logging

# Configurar logging
setup_logging()
logger = logging.getLogger("discord-bot")


async def main():
    """Função principal de inicialização do bot."""
    logger.info("🚀 Iniciando Discord AI Bot v2...")
    logger.info(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Carregar configurações
    config = Config()
    
    # Verificar token
    if not config.bot_token:
        logger.error("❌ DISCORD_BOT_TOKEN não configurado!")
        logger.error("Por favor, defina a variável de ambiente DISCORD_BOT_TOKEN")
        return
    
    # Inicializar banco de dados
    db = DatabaseManager(config.db_path)
    await db.initialize()
    
    # Criar e iniciar o bot
    bot = BotInstance(config, db)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("⛔ Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}", exc_info=True)
    finally:
        await bot.cleanup()
        logger.info("👋 Bot encerrado")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"💥 Erro crítico: {e}", exc_info=True)
        sys.exit(1)
