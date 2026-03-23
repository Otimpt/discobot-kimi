"""
Manipulador de Imagens
Download e envio correto de imagens no Discord
"""

import os
import re
import aiohttp
import logging
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

import discord

logger = logging.getLogger("discord-bot")


class ImageHandler:
    """Manipula imagens para envio correto no Discord."""
    
    def __init__(self, temp_dir: str = "data/temp_images"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Extensões suportadas
        self.supported_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}
    
    async def process_image_url(self, url: str) -> Optional[Tuple[str, str]]:
        """
        Processa uma URL de imagem e retorna o caminho local e o nome do arquivo.
        
        Args:
            url: URL da imagem
            
        Returns:
            Tupla (caminho_local, nome_arquivo) ou None se falhar
        """
        try:
            # Verificar se é uma URL válida
            if not self._is_valid_url(url):
                logger.warning(f"URL inválida: {url}")
                return None
            
            # Determinar extensão do arquivo
            extension = self._get_extension_from_url(url)
            
            # Gerar nome único
            filename = f"img_{hash(url) % 10000000:07d}{extension}"
            filepath = self.temp_dir / filename
            
            # Download da imagem
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        logger.warning(f"Falha ao baixar imagem: {response.status}")
                        return None
                    
                    # Verificar content type
                    content_type = response.headers.get('content-type', '')
                    if not content_type.startswith('image/'):
                        logger.warning(f"Content-type não é imagem: {content_type}")
                        return None
                    
                    # Salvar arquivo
                    content = await response.read()
                    filepath.write_bytes(content)
                    
                    logger.info(f"Imagem baixada: {filename} ({len(content)} bytes)")
                    return (str(filepath), filename)
        
        except Exception as e:
            logger.error(f"Erro ao processar imagem {url}: {e}")
            return None
    
    async def create_discord_file(self, url: str) -> Optional[discord.File]:
        """
        Cria um discord.File a partir de uma URL.
        
        Args:
            url: URL da imagem
            
        Returns:
            discord.File ou None se falhar
        """
        result = await self.process_image_url(url)
        if not result:
            return None
        
        filepath, filename = result
        
        try:
            return discord.File(filepath, filename=filename)
        except Exception as e:
            logger.error(f"Erro ao criar discord.File: {e}")
            return None
    
    def _is_valid_url(self, url: str) -> bool:
        """Verifica se é uma URL válida."""
        try:
            result = urlparse(url)
            return all([result.scheme in ['http', 'https'], result.netloc])
        except:
            return False
    
    def _get_extension_from_url(self, url: str) -> str:
        """Extrai a extensão da URL."""
        # Tentar extrair da URL
        parsed = urlparse(url)
        path = parsed.path
        
        if path:
            ext = Path(path).suffix.lower()
            if ext in self.supported_extensions:
                return ext
        
        # Tentar extrair de query params
        if 'format=' in url:
            match = re.search(r'format=(\w+)', url)
            if match:
                ext = f".{match.group(1).lower()}"
                if ext in self.supported_extensions:
                    return ext
        
        # Padrão
        return '.png'
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Remove arquivos antigos do diretório temporário."""
        try:
            from datetime import datetime, timedelta
            cutoff = datetime.now() - timedelta(hours=max_age_hours)
            
            for filepath in self.temp_dir.iterdir():
                if filepath.is_file():
                    mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                    if mtime < cutoff:
                        filepath.unlink()
                        logger.debug(f"Arquivo removido: {filepath.name}")
        
        except Exception as e:
            logger.error(f"Erro ao limpar arquivos antigos: {e}")
    
    async def extract_image_urls(self, text: str) -> list:
        """Extrai URLs de imagem de um texto."""
        # Padrões comuns de URL de imagem
        patterns = [
            r'https?://[^\s<>"{}|\\^`\[\]]+\.(?:png|jpg|jpeg|gif|webp|bmp)',
            r'https?://(?:cdn\.discordapp\.com|media\.discordapp\.net)/[^\s<>"{}|\\^`\[\]]+',
            r'https?://(?:i\.imgur\.com|imgur\.com)/[^\s<>"{}|\\^`\[\]]+',
        ]
        
        urls = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            urls.update(matches)
        
        return list(urls)
    
    async def process_message_images(self, content: str) -> Tuple[str, list]:
        """
        Processa imagens em uma mensagem e retorna o texto limpo + arquivos.
        
        Args:
            content: Conteúdo da mensagem
            
        Returns:
            Tupla (texto_limpo, lista_de_arquivos)
        """
        urls = await self.extract_image_urls(content)
        files = []
        
        for url in urls:
            file = await self.create_discord_file(url)
            if file:
                files.append(file)
                # Remover URL do texto
                content = content.replace(url, '')
        
        # Limpar texto
        content = content.strip()
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content, files


# Instância global
image_handler = ImageHandler()
