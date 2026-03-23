"""
Comandos de Arquivos
Gerenciamento de uploads e arquivos
"""

import logging
import os
from pathlib import Path
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from core.config import Config
from database.manager import DatabaseManager
from utils.permission_checker import PermissionChecker, permission_denied_message

logger = logging.getLogger("discord-bot")


class FileCommands(commands.Cog):
    """Comandos para gerenciar arquivos."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config
        self.db: DatabaseManager = bot.db
        self.permission = PermissionChecker(self.config)
        self.uploads_dir = Path("data/uploads")
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
    
    arquivo_group = app_commands.Group(
        name="arquivo",
        description="Gerenciamento de arquivos"
    )
    
    @arquivo_group.command(name="enviar", description="Envia um arquivo para o bot")
    @app_commands.describe(
        arquivo="Arquivo a enviar",
        privado="Se o arquivo deve ser privado (só você pode acessar)"
    )
    async def file_upload(
        self,
        interaction: discord.Interaction,
        arquivo: discord.Attachment,
        privado: bool = False
    ):
        """Envia um arquivo."""
        if not self.permission.check_permissions(interaction):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        # Verificar tamanho (max 25MB)
        if arquivo.size > 25 * 1024 * 1024:
            await interaction.response.send_message(
                "❌ Arquivo muito grande. Máximo: 25MB",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Criar diretório do usuário
            user_dir = self.uploads_dir / str(interaction.user.id)
            user_dir.mkdir(exist_ok=True)
            
            # Salvar arquivo
            file_path = user_dir / arquivo.filename
            await arquivo.save(file_path)
            
            # Registrar no banco
            upload_id = await self.db.add_upload(
                filename=arquivo.filename,
                file_path=str(file_path),
                content_type=arquivo.content_type or "unknown",
                file_size=arquivo.size,
                user_id=interaction.user.id,
                channel_id=interaction.channel_id,
                guild_id=interaction.guild_id,
                is_private=privado
            )
            
            embed = discord.Embed(
                title="✅ Arquivo Enviado",
                description=f"**{arquivo.filename}** salvo com sucesso!",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Tamanho",
                value=f"{arquivo.size / 1024:.1f} KB",
                inline=True
            )
            embed.add_field(
                name="Privado",
                value="Sim" if privado else "Não",
                inline=True
            )
            embed.add_field(
                name="ID",
                value=str(upload_id),
                inline=True
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro ao enviar arquivo: {e}")
            await interaction.followup.send(
                f"❌ Erro ao enviar arquivo: {e}",
                ephemeral=True
            )
    
    @arquivo_group.command(name="listar", description="Lista seus arquivos")
    async def file_list(self, interaction: discord.Interaction):
        """Lista arquivos do usuário."""
        uploads = await self.db.get_uploads(user_id=interaction.user.id)
        
        if not uploads:
            await interaction.response.send_message(
                "📭 Você não tem arquivos enviados.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="📁 Seus Arquivos",
            color=discord.Color.blue()
        )
        
        for upload in uploads[:10]:  # Mostrar últimos 10
            size_kb = upload["file_size"] / 1024
            embed.add_field(
                name=f"{upload['filename']} (ID: {upload['id']})",
                value=f"Tamanho: {size_kb:.1f} KB | "
                      f"{'🔒 Privado' if upload['is_private'] else '📂 Público'}",
                inline=False
            )
        
        if len(uploads) > 10:
            embed.set_footer(text=f"E mais {len(uploads) - 10} arquivos...")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @arquivo_group.command(name="baixar", description="Baixa um arquivo pelo ID")
    @app_commands.describe(arquivo_id="ID do arquivo")
    async def file_download(
        self,
        interaction: discord.Interaction,
        arquivo_id: int
    ):
        """Baixa um arquivo."""
        upload = await self.db.get_upload_by_id(arquivo_id)
        
        if not upload:
            await interaction.response.send_message(
                "❌ Arquivo não encontrado.",
                ephemeral=True
            )
            return
        
        # Verificar permissão
        if upload["is_private"] and upload["user_id"] != interaction.user.id:
            await interaction.response.send_message(
                "🔒 Este arquivo é privado.",
                ephemeral=True
            )
            return
        
        file_path = Path(upload["file_path"])
        
        if not file_path.exists():
            await interaction.response.send_message(
                "❌ Arquivo não encontrado no servidor.",
                ephemeral=True
            )
            return
        
        # Enviar arquivo
        await interaction.response.send_message(
            content=f"📎 **{upload['filename']}**:",
            file=discord.File(file_path, upload["filename"]),
            ephemeral=upload["is_private"]
        )
    
    @arquivo_group.command(name="apagar", description="Remove um arquivo")
    @app_commands.describe(arquivo_id="ID do arquivo")
    async def file_delete(
        self,
        interaction: discord.Interaction,
        arquivo_id: int
    ):
        """Remove um arquivo."""
        upload = await self.db.get_upload_by_id(arquivo_id)
        
        if not upload:
            await interaction.response.send_message(
                "❌ Arquivo não encontrado.",
                ephemeral=True
            )
            return
        
        # Verificar permissão
        if upload["user_id"] != interaction.user.id:
            # Verificar se é admin
            if not self.permission.is_admin(interaction.user, interaction.guild):
                await interaction.response.send_message(
                    "❌ Você não tem permissão para apagar este arquivo.",
                    ephemeral=True
                )
                return
        
        # Apagar arquivo
        file_path = Path(upload["file_path"])
        if file_path.exists():
            file_path.unlink()
        
        # Remover do banco
        await self.db._connection.execute(
            "DELETE FROM uploads WHERE id = ?",
            (arquivo_id,)
        )
        await self.db._connection.commit()
        
        await interaction.response.send_message(
            f"🗑️ Arquivo **{upload['filename']}** removido.",
            ephemeral=True
        )
    
    @arquivo_group.command(name="compartilhar", description="Compartilha um arquivo no chat")
    @app_commands.describe(arquivo_id="ID do arquivo")
    async def file_share(
        self,
        interaction: discord.Interaction,
        arquivo_id: int
    ):
        """Compartilha um arquivo no chat."""
        upload = await self.db.get_upload_by_id(arquivo_id)
        
        if not upload:
            await interaction.response.send_message(
                "❌ Arquivo não encontrado.",
                ephemeral=True
            )
            return
        
        # Verificar permissão
        if upload["user_id"] != interaction.user.id:
            await interaction.response.send_message(
                "❌ Você não tem permissão para compartilhar este arquivo.",
                ephemeral=True
            )
            return
        
        file_path = Path(upload["file_path"])
        
        if not file_path.exists():
            await interaction.response.send_message(
                "❌ Arquivo não encontrado no servidor.",
                ephemeral=True
            )
            return
        
        # Enviar publicamente
        await interaction.response.send_message(
            content=f"📎 {interaction.user.mention} compartilhou **{upload['filename']}**:",
            file=discord.File(file_path, upload["filename"])
        )


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(FileCommands(bot))
