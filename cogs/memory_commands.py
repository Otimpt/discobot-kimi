"""
Comandos de Memória
Gerenciamento de memória e fatos
"""

import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from core.config import Config
from database.manager import DatabaseManager
from utils.permission_checker import PermissionChecker, permission_denied_message

logger = logging.getLogger("discord-bot")


class MemoryCommands(commands.Cog):
    """Comandos para gerenciar memória."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config
        self.db: DatabaseManager = bot.db
        self.permission = PermissionChecker(self.config)
    
    memoria_group = app_commands.Group(
        name="memoria",
        description="Gerenciamento de memória"
    )
    
    @memoria_group.command(name="adicionar", description="Adiciona um fato à memória")
    @app_commands.describe(
        fato="Fato a ser lembrado",
        tipo="Tipo de memória"
    )
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Sobre mim", value="user"),
        app_commands.Choice(name="Sobre o servidor", value="guild"),
    ])
    async def memory_add(
        self,
        interaction: discord.Interaction,
        fato: str,
        tipo: app_commands.Choice[str]
    ):
        """Adiciona fato à memória."""
        if not self.permission.check_permissions(interaction):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        if tipo.value == "user":
            await self.db.add_user_fact(
                user_id=interaction.user.id,
                fact=fato,
                importance=1.0,
                is_permanent=False
            )
            target = "suas memórias"
        else:
            if not interaction.guild:
                await interaction.response.send_message(
                    "❌ Este tipo de memória só funciona em servidores.",
                    ephemeral=True
                )
                return
            
            await self.db.add_guild_fact(
                guild_id=interaction.guild.id,
                fact=fato,
                importance=1.0,
                is_permanent=False
            )
            target = "memórias do servidor"
        
        await interaction.response.send_message(
            f"✅ Fato adicionado a {target}:\n```{fato}```",
            ephemeral=True
        )
    
    @memoria_group.command(name="ver", description="Mostra fatos armazenados")
    @app_commands.describe(
        tipo="Tipo de memória",
        usuario="Usuário (para memórias de usuário)"
    )
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Minhas memórias", value="user"),
        app_commands.Choice(name="Memórias do servidor", value="guild"),
    ])
    async def memory_view(
        self,
        interaction: discord.Interaction,
        tipo: app_commands.Choice[str],
        usuario: Optional[discord.Member] = None
    ):
        """Mostra memórias."""
        if tipo.value == "user":
            target_user = usuario or interaction.user
            facts = await self.db.get_user_facts(target_user.id, limit=20)
            title = f"🧠 Memórias de {target_user.display_name}"
        else:
            if not interaction.guild:
                await interaction.response.send_message(
                    "❌ Este tipo de memória só funciona em servidores.",
                    ephemeral=True
                )
                return
            
            facts = await self.db.get_guild_facts(interaction.guild.id, limit=20)
            title = f"🧠 Memórias de {interaction.guild.name}"
        
        if not facts:
            await interaction.response.send_message(
                "📭 Nenhuma memória encontrada.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=title,
            color=discord.Color.blue()
        )
        
        for i, fact in enumerate(facts, 1):
            embed.add_field(
                name=f"{i}. {fact['created_at'][:10] if fact.get('created_at') else 'Data desconhecida'}",
                value=fact['fact'][:200] + "..." if len(fact['fact']) > 200 else fact['fact'],
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @memoria_group.command(name="apagar", description="Remove um fato da memória")
    @app_commands.describe(indice="Índice do fato (use /memoria ver para ver os índices)")
    async def memory_delete(
        self,
        interaction: discord.Interaction,
        indice: int
    ):
        """Remove fato da memória."""
        # Obter fatos do usuário
        facts = await self.db.get_user_facts(interaction.user.id, limit=50)
        
        if indice < 1 or indice > len(facts):
            await interaction.response.send_message(
                f"❌ Índice inválido. Use `/memoria ver` para ver seus fatos.",
                ephemeral=True
            )
            return
        
        fact = facts[indice - 1]
        
        # Apagar do banco
        await self.db._connection.execute(
            "DELETE FROM user_facts WHERE id = ? AND user_id = ?",
            (fact["id"], interaction.user.id)
        )
        await self.db._connection.commit()
        
        await interaction.response.send_message(
            f"✅ Fato removido:\n```{fact['fact'][:100]}...```" if len(fact['fact']) > 100 else f"✅ Fato removido:\n```{fact['fact']}```",
            ephemeral=True
        )
    
    @memoria_group.command(name="limpar", description="Limpa todas as suas memórias")
    async def memory_clear(self, interaction: discord.Interaction):
        """Limpa todas as memórias do usuário."""
        # Confirmar
        embed = discord.Embed(
            title="⚠️ Confirmar",
            description="Tem certeza que deseja apagar TODAS as suas memórias?\n"
                       "Esta ação não pode ser desfeita.",
            color=discord.Color.red()
        )
        
        view = discord.ui.View()
        
        async def confirm_callback(interaction_callback: discord.Interaction):
            await self.db._connection.execute(
                "DELETE FROM user_facts WHERE user_id = ?",
                (interaction.user.id,)
            )
            await self.db._connection.commit()
            
            await interaction_callback.response.send_message(
                "✅ Todas as suas memórias foram apagadas.",
                ephemeral=True
            )
        
        async def cancel_callback(interaction_callback: discord.Interaction):
            await interaction_callback.response.send_message(
                "❌ Operação cancelada.",
                ephemeral=True
            )
        
        confirm_btn = discord.ui.Button(
            label="Sim, apagar tudo",
            style=discord.ButtonStyle.danger
        )
        confirm_btn.callback = confirm_callback
        
        cancel_btn = discord.ui.Button(
            label="Cancelar",
            style=discord.ButtonStyle.secondary
        )
        cancel_btn.callback = cancel_callback
        
        view.add_item(confirm_btn)
        view.add_item(cancel_btn)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @memoria_group.command(name="importancia", description="Define importância de um fato")
    @app_commands.describe(
        indice="Índice do fato",
        importancia="Importância (1-10)"
    )
    async def memory_importance(
        self,
        interaction: discord.Interaction,
        indice: int,
        importancia: int
    ):
        """Define importância de um fato."""
        if importancia < 1 or importancia > 10:
            await interaction.response.send_message(
                "❌ Importância deve ser entre 1 e 10.",
                ephemeral=True
            )
            return
        
        facts = await self.db.get_user_facts(interaction.user.id, limit=50)
        
        if indice < 1 or indice > len(facts):
            await interaction.response.send_message(
                f"❌ Índice inválido.",
                ephemeral=True
            )
            return
        
        fact = facts[indice - 1]
        
        await self.db._connection.execute(
            "UPDATE user_facts SET importance = ? WHERE id = ?",
            (importancia / 10.0, fact["id"])
        )
        await self.db._connection.commit()
        
        await interaction.response.send_message(
            f"✅ Importância do fato atualizada para {importancia}/10.",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(MemoryCommands(bot))
