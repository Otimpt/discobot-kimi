"""
Gerenciador de Status do Bot
Suporta rotação automática de status personalizados
"""

import random
import asyncio
from typing import List, Dict, Optional
from datetime import datetime

import discord

from core.config import Config


class StatusManager:
    """Gerencia os status/presença do bot."""
    
    DEFAULT_STATUSES = [
        {"type": "watching", "text": "🤖 IA Avançada | /ajuda"},
        {"type": "playing", "text": "💬 Conversas Inteligentes"},
        {"type": "listening", "text": "🎭 Personas Customizáveis"},
        {"type": "watching", "text": "🖼️ Geração de Imagens"},
        {"type": "playing", "text": "🧠 Memória de Longo Prazo"},
        {"type": "listening", "text": "🔧 Modo Assistant API"},
        {"type": "competing", "text": "🏆 Servidores: {guild_count}"},
        {"type": "watching", "text": "👥 Usuários: {user_count}"},
        {"type": "playing", "text": "⚡ Múltiplos Modelos LLM"},
        {"type": "listening", "text": "💡 Dúvidas? Use /ajuda"},
    ]
    
    def __init__(self, client: discord.Client, config: Config):
        self.client = client
        self.config = config
        self.statuses: List[Dict] = []
        self.current_index = 0
        self._rotation_task: Optional[asyncio.Task] = None
        
    async def start_rotation(self, interval_minutes: int = 5):
        """Inicia a rotação automática de status."""
        self.statuses = self.DEFAULT_STATUSES.copy()
        await self._update_status()
    
    async def rotate_status(self):
        """Rotaciona para o próximo status."""
        if not self.statuses:
            return
        
        self.current_index = (self.current_index + 1) % len(self.statuses)
        await self._update_status()
    
    async def _update_status(self):
        """Atualiza o status atual do bot."""
        if not self.statuses:
            return
        
        status_data = self.statuses[self.current_index]
        
        # Substituir variáveis
        text = status_data["text"]
        text = text.replace("{guild_count}", str(len(self.client.guilds)))
        text = text.replace("{user_count}", str(sum(g.member_count for g in self.client.guilds)))
        text = text.replace("{timestamp}", datetime.now().strftime("%H:%M"))
        
        # Criar atividade
        activity_type = self._get_activity_type(status_data["type"])
        activity = discord.Activity(type=activity_type, name=text)
        
        await self.client.change_presence(activity=activity)
    
    def _get_activity_type(self, type_str: str) -> discord.ActivityType:
        """Converte string para tipo de atividade."""
        type_map = {
            "playing": discord.ActivityType.playing,
            "listening": discord.ActivityType.listening,
            "watching": discord.ActivityType.watching,
            "competing": discord.ActivityType.competing,
        }
        return type_map.get(type_str.lower(), discord.ActivityType.playing)
    
    def add_custom_status(self, text: str, status_type: str = "watching"):
        """Adiciona um status customizado."""
        self.statuses.append({
            "type": status_type,
            "text": text
        })
    
    def remove_status(self, index: int):
        """Remove um status pelo índice."""
        if 0 <= index < len(self.statuses):
            self.statuses.pop(index)
            if self.current_index >= len(self.statuses):
                self.current_index = 0
    
    async def set_temporary_status(
        self,
        text: str,
        status_type: str = "watching",
        duration_seconds: int = 60
    ):
        """Define um status temporário."""
        # Salvar status atual
        old_index = self.current_index
        
        # Aplicar status temporário
        activity_type = self._get_activity_type(status_type)
        activity = discord.Activity(type=activity_type, name=text)
        await self.client.change_presence(activity=activity)
        
        # Aguardar e restaurar
        await asyncio.sleep(duration_seconds)
        self.current_index = old_index
        await self._update_status()
