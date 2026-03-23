"""
Manipulador de Respostas
Gerencia envio de mensagens (embed ou texto) com formatação correta
"""

import logging
from typing import Optional, List, Union, Dict, Any
from enum import Enum

import discord
from discord.ext import commands

from utils.discord_formatter import formatter
from utils.image_handler import image_handler

logger = logging.getLogger("discord-bot")


class ResponseType(Enum):
    """Tipos de resposta."""
    TEXT = "text"           # Texto simples
    EMBED = "embed"         # Embed
    AUTO = "auto"           # Decidir automaticamente


class ResponseHandler:
    """Manipula o envio de respostas do bot."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.default_type = ResponseType.EMBED
    
    async def send_response(
        self,
        destination: Union[discord.TextChannel, discord.Thread, discord.Interaction, discord.Message],
        content: str,
        response_type: Optional[ResponseType] = None,
        title: Optional[str] = None,
        color: discord.Color = discord.Color.blue(),
        footer: Optional[str] = None,
        files: Optional[List[discord.File]] = None,
        view: Optional[discord.ui.View] = None,
        ephemeral: bool = False,
        mention_author: bool = False
    ) -> Optional[Union[discord.Message, List[discord.Message]]]:
        """
        Envia uma resposta formatada.
        
        Args:
            destination: Onde enviar (canal, thread, interaction, ou mensagem para reply)
            content: Conteúdo da mensagem
            response_type: Tipo de resposta (TEXT, EMBED, AUTO)
            title: Título (para embeds)
            color: Cor do embed
            footer: Rodapé do embed
            files: Arquivos para anexar
            view: View com componentes
            ephemeral: Se a mensagem deve ser efêmera (só para interactions)
            mention_author: Se deve mencionar o autor (só para replies)
            
        Returns:
            Mensagem(ns) enviada(s) ou None
        """
        try:
            # Determinar tipo de resposta
            if response_type is None:
                response_type = self.default_type
            
            # Formatar conteúdo
            content = formatter.format_text(content)
            
            # Processar imagens no conteúdo
            processed_content, image_files = await image_handler.process_message_images(content)
            
            # Combinar arquivos
            all_files = (files or []) + image_files
            
            # Decidir tipo automaticamente se necessário
            if response_type == ResponseType.AUTO:
                response_type = self._auto_select_type(processed_content, title)
            
            # Enviar conforme o tipo
            if response_type == ResponseType.TEXT:
                return await self._send_text(
                    destination, processed_content, all_files, view, ephemeral, mention_author
                )
            else:
                return await self._send_embed(
                    destination, processed_content, title, color, footer, 
                    all_files, view, ephemeral, mention_author
                )
        
        except Exception as e:
            logger.error(f"Erro ao enviar resposta: {e}")
            return None
    
    def _auto_select_type(
        self, 
        content: str, 
        title: Optional[str] = None
    ) -> ResponseType:
        """Seleciona automaticamente o tipo de resposta."""
        # Se tiver título, usar embed
        if title:
            return ResponseType.EMBED
        
        # Se for muito curto, usar texto
        if len(content) < 100 and '\n' not in content:
            return ResponseType.TEXT
        
        # Se tiver múltiplas linhas ou formatação, usar embed
        if '\n' in content or '**' in content or '`' in content:
            return ResponseType.EMBED
        
        # Padrão: embed
        return ResponseType.EMBED
    
    async def _send_text(
        self,
        destination: Union[discord.TextChannel, discord.Thread, discord.Interaction, discord.Message],
        content: str,
        files: Optional[List[discord.File]] = None,
        view: Optional[discord.ui.View] = None,
        ephemeral: bool = False,
        mention_author: bool = False
    ) -> Optional[Union[discord.Message, List[discord.Message]]]:
        """Envia resposta como texto."""
        # Dividir se necessário
        if len(content) > formatter.MAX_MESSAGE_LENGTH:
            parts = formatter.split_long_message(content)
            messages = []
            
            for i, part in enumerate(parts):
                # Só anexar arquivos na primeira mensagem
                part_files = files if i == 0 else None
                
                msg = await self._send_to_destination(
                    destination, part, part_files, view if i == len(parts) - 1 else None,
                    ephemeral, mention_author
                )
                
                if msg:
                    messages.append(msg)
            
            return messages
        
        return await self._send_to_destination(
            destination, content, files, view, ephemeral, mention_author
        )
    
    async def _send_embed(
        self,
        destination: Union[discord.TextChannel, discord.Thread, discord.Interaction, discord.Message],
        content: str,
        title: Optional[str] = None,
        color: discord.Color = discord.Color.blue(),
        footer: Optional[str] = None,
        files: Optional[List[discord.File]] = None,
        view: Optional[discord.ui.View] = None,
        ephemeral: bool = False,
        mention_author: bool = False
    ) -> Optional[Union[discord.Message, List[discord.Message]]]:
        """Envia resposta como embed."""
        # Criar embed
        embed = formatter.create_embed(
            title=title,
            description=content,
            color=color,
            footer=footer
        )
        
        # Verificar se precisa dividir
        total_length = len(content) + len(title or "") + len(footer or "")
        
        if total_length > formatter.MAX_EMBED_TOTAL:
            # Dividir em múltiplos embeds
            return await self._send_split_embeds(
                destination, content, title, color, footer, files, view, ephemeral, mention_author
            )
        
        return await self._send_embed_to_destination(
            destination, embed, files, view, ephemeral, mention_author
        )
    
    async def _send_split_embeds(
        self,
        destination: Union[discord.TextChannel, discord.Thread, discord.Interaction, discord.Message],
        content: str,
        title: Optional[str] = None,
        color: discord.Color = discord.Color.blue(),
        footer: Optional[str] = None,
        files: Optional[List[discord.File]] = None,
        view: Optional[discord.ui.View] = None,
        ephemeral: bool = False,
        mention_author: bool = False
    ) -> List[discord.Message]:
        """Envia conteúdo dividido em múltiplos embeds."""
        parts = formatter.split_long_message(content, formatter.MAX_EMBED_DESCRIPTION)
        messages = []
        
        for i, part in enumerate(parts):
            part_title = f"{title} (parte {i+1}/{len(parts)})" if title and len(parts) > 1 else title
            part_footer = footer if i == len(parts) - 1 else f"Continua na próxima mensagem..."
            part_files = files if i == 0 else None
            part_view = view if i == len(parts) - 1 else None
            
            embed = formatter.create_embed(
                title=part_title,
                description=part,
                color=color,
                footer=part_footer
            )
            
            msg = await self._send_embed_to_destination(
                destination, embed, part_files, part_view, ephemeral, mention_author
            )
            
            if msg:
                messages.append(msg)
        
        return messages
    
    async def _send_to_destination(
        self,
        destination: Union[discord.TextChannel, discord.Thread, discord.Interaction, discord.Message],
        content: str,
        files: Optional[List[discord.File]] = None,
        view: Optional[discord.ui.View] = None,
        ephemeral: bool = False,
        mention_author: bool = False
    ) -> Optional[discord.Message]:
        """Envia para o destino apropriado."""
        kwargs = {
            "content": content,
            "files": files or [],
            "view": view
        }
        
        # Interaction
        if isinstance(destination, discord.Interaction):
            if destination.response.is_done():
                return await destination.followup.send(
                    **kwargs, ephemeral=ephemeral
                )
            else:
                await destination.response.send_message(
                    **kwargs, ephemeral=ephemeral
                )
                return None
        
        # Reply para mensagem
        if isinstance(destination, discord.Message):
            return await destination.reply(
                **kwargs, mention_author=mention_author
            )
        
        # Canal ou Thread
        return await destination.send(**kwargs)
    
    async def _send_embed_to_destination(
        self,
        destination: Union[discord.TextChannel, discord.Thread, discord.Interaction, discord.Message],
        embed: discord.Embed,
        files: Optional[List[discord.File]] = None,
        view: Optional[discord.ui.View] = None,
        ephemeral: bool = False,
        mention_author: bool = False
    ) -> Optional[discord.Message]:
        """Envia embed para o destino apropriado."""
        kwargs = {
            "embed": embed,
            "files": files or [],
            "view": view
        }
        
        # Interaction
        if isinstance(destination, discord.Interaction):
            if destination.response.is_done():
                return await destination.followup.send(
                    **kwargs, ephemeral=ephemeral
                )
            else:
                await destination.response.send_message(
                    **kwargs, ephemeral=ephemeral
                )
                return None
        
        # Reply para mensagem
        if isinstance(destination, discord.Message):
            return await destination.reply(
                **kwargs, mention_author=mention_author
            )
        
        # Canal ou Thread
        return await destination.send(**kwargs)
    
    # === Métodos de conveniência ===
    
    async def send_success(
        self,
        destination: Union[discord.TextChannel, discord.Thread, discord.Interaction, discord.Message],
        content: str,
        title: str = "✅ Sucesso!",
        **kwargs
    ):
        """Envia mensagem de sucesso."""
        return await self.send_response(
            destination, content,
            title=title,
            color=discord.Color.green(),
            **kwargs
        )
    
    async def send_error(
        self,
        destination: Union[discord.TextChannel, discord.Thread, discord.Interaction, discord.Message],
        content: str,
        title: str = "❌ Erro!",
        **kwargs
    ):
        """Envia mensagem de erro."""
        return await self.send_response(
            destination, content,
            title=title,
            color=discord.Color.red(),
            **kwargs
        )
    
    async def send_warning(
        self,
        destination: Union[discord.TextChannel, discord.Thread, discord.Interaction, discord.Message],
        content: str,
        title: str = "⚠️ Aviso!",
        **kwargs
    ):
        """Envia mensagem de aviso."""
        return await self.send_response(
            destination, content,
            title=title,
            color=discord.Color.yellow(),
            **kwargs
        )
    
    async def send_info(
        self,
        destination: Union[discord.TextChannel, discord.Thread, discord.Interaction, discord.Message],
        content: str,
        title: str = "ℹ️ Informação",
        **kwargs
    ):
        """Envia mensagem informativa."""
        return await self.send_response(
            destination, content,
            title=title,
            color=discord.Color.blue(),
            **kwargs
        )


# Instância global (será inicializada com o bot)
response_handler: Optional[ResponseHandler] = None


def setup_response_handler(bot: commands.Bot):
    """Inicializa o response handler."""
    global response_handler
    response_handler = ResponseHandler(bot)
    logger.info("Response handler inicializado")
