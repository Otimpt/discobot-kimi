"""
Comandos de Personas
Gerenciamento de personas e personalidades
"""

import json
import logging
from typing import Optional

import discord
from discord import app_commands, ui
from discord.ext import commands

from core.config import Config
from database.manager import DatabaseManager
from utils.permission_checker import PermissionChecker, permission_denied_message

logger = logging.getLogger("discord-bot")


class PersonaCommands(commands.Cog):
    """Comandos para gerenciar personas."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config
        self.db: DatabaseManager = bot.db
        self.permission = PermissionChecker(self.config)
    
    persona_group = app_commands.Group(
        name="persona",
        description="Gerenciamento de personas"
    )
    
    @persona_group.command(name="listar", description="Lista todas as personas disponíveis")
    async def persona_list(self, interaction: discord.Interaction):
        """Lista personas disponíveis."""
        personas = await self.db.list_personas(interaction.guild_id if interaction.guild else None)
        
        if not personas:
            await interaction.response.send_message(
                "📭 Nenhuma persona encontrada.\n"
                "Use `/persona criar` para criar uma nova.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🎭 Personas Disponíveis",
            description="Use `/persona usar <nome>` para ativar",
            color=discord.Color.purple()
        )
        
        # Separar por tipo
        globals_p = [p for p in personas if p.get("is_global")]
        locals_p = [p for p in personas if not p.get("is_global")]
        
        if globals_p:
            global_text = "\n".join([
                f"• **{p['name']}**" + (f" - {p['description'][:50]}..." if p.get("description") else "")
                for p in globals_p
            ])
            embed.add_field(name="🌍 Globais", value=global_text, inline=False)
        
        if locals_p:
            local_text = "\n".join([
                f"• **{p['name']}**" + (f" - {p['description'][:50]}..." if p.get("description") else "")
                for p in locals_p[:10]
            ])
            embed.add_field(name="🏠 Deste Servidor", value=local_text, inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @persona_group.command(name="criar", description="Cria uma nova persona")
    @app_commands.describe(
        nome="Nome da persona",
        prompt="System prompt que define a personalidade",
        descricao="Descrição curta (opcional)",
        prompt_id="OpenAI Prompt ID (opcional)"
    )
    async def persona_create(
        self,
        interaction: discord.Interaction,
        nome: str,
        prompt: str,
        descricao: Optional[str] = None,
        prompt_id: Optional[str] = None
    ):
        """Cria uma nova persona."""
        if not self.permission.check_permissions(interaction, admin_only=True):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        await self.db.create_persona(
            guild_id=interaction.guild_id,
            name=nome,
            system_prompt=prompt,
            prompt_id=prompt_id,
            description=descricao,
            created_by=interaction.user.id
        )
        
        embed = discord.Embed(
            title="✅ Persona Criada",
            description=f"Persona **{nome}** criada com sucesso!",
            color=discord.Color.green()
        )
        
        if descricao:
            embed.add_field(name="Descrição", value=descricao, inline=False)
        
        if prompt_id:
            embed.add_field(name="Prompt ID", value=prompt_id, inline=True)
        
        embed.add_field(
            name="Próximo passo",
            value=f"Use `/persona usar {nome}` para ativar",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @persona_group.command(name="usar", description="Ativa uma persona neste canal")
    @app_commands.describe(nome="Nome da persona")
    @app_commands.autocomplete(nome=lambda interaction, current: [
        app_commands.Choice(name=p["name"], value=p["name"])
        for p in interaction.client.db.list_personas(interaction.guild_id if interaction.guild else None)
        if current.lower() in p["name"].lower()
    ][:25])
    async def persona_use(
        self,
        interaction: discord.Interaction,
        nome: str
    ):
        """Ativa uma persona."""
        if not self.permission.check_permissions(interaction, admin_only=True):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        persona = await self.db.get_persona(nome, interaction.guild_id if interaction.guild else None)
        
        if not persona:
            await interaction.response.send_message(
                f"❌ Persona '{nome}' não encontrada.",
                ephemeral=True
            )
            return
        
        # Ativar no canal
        await self.db.set_channel_settings(
            interaction.channel_id,
            interaction.guild_id,
            persona_id=nome,
            system_prompt=persona.get("system_prompt"),
            prompt_id=persona.get("prompt_id")
        )
        
        embed = discord.Embed(
            title="🎭 Persona Ativada",
            description=f"Persona **{nome}** está ativa neste canal!",
            color=discord.Color.purple()
        )
        
        if persona.get("description"):
            embed.add_field(name="Descrição", value=persona["description"], inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @persona_group.command(name="parar", description="Desativa a persona atual")
    async def persona_stop(self, interaction: discord.Interaction):
        """Desativa a persona atual."""
        if not self.permission.check_permissions(interaction, admin_only=True):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        settings = await self.db.get_channel_settings(interaction.channel_id)
        current_persona = settings.get("persona_id")
        
        if not current_persona:
            await interaction.response.send_message(
                "ℹ️ Nenhuma persona ativa neste canal.",
                ephemeral=True
            )
            return
        
        await self.db.set_channel_settings(
            interaction.channel_id,
            interaction.guild_id,
            persona_id=None,
            system_prompt=None,
            prompt_id=None
        )
        
        await interaction.response.send_message(
            f"🎭 Persona **{current_persona}** desativada.",
            ephemeral=True
        )
    
    @persona_group.command(name="info", description="Mostra informações sobre uma persona")
    @app_commands.describe(nome="Nome da persona")
    async def persona_info(
        self,
        interaction: discord.Interaction,
        nome: str
    ):
        """Mostra informações de uma persona."""
        persona = await self.db.get_persona(nome, interaction.guild_id if interaction.guild else None)
        
        if not persona:
            await interaction.response.send_message(
                f"❌ Persona '{nome}' não encontrada.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f"🎭 {persona['name']}",
            description=persona.get("description", "Sem descrição"),
            color=discord.Color.purple()
        )
        
        prompt_preview = persona.get("system_prompt", "")[:500]
        if len(persona.get("system_prompt", "")) > 500:
            prompt_preview += "..."
        
        embed.add_field(
            name="System Prompt",
            value=f"```{prompt_preview}```",
            inline=False
        )
        
        if persona.get("prompt_id"):
            embed.add_field(
                name="OpenAI Prompt ID",
                value=persona["prompt_id"],
                inline=True
            )
        
        if persona.get("is_global"):
            embed.add_field(name="Tipo", value="🌍 Global", inline=True)
        else:
            embed.add_field(name="Tipo", value="🏠 Servidor", inline=True)
        
        created_at = persona.get("created_at")
        if created_at:
            embed.set_footer(text=f"Criada em: {created_at}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @persona_group.command(name="apagar", description="Remove uma persona")
    @app_commands.describe(nome="Nome da persona")
    async def persona_delete(
        self,
        interaction: discord.Interaction,
        nome: str
    ):
        """Remove uma persona."""
        if not self.permission.check_permissions(interaction, admin_only=True):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        persona = await self.db.get_persona(nome, interaction.guild_id)
        
        if not persona:
            await interaction.response.send_message(
                f"❌ Persona '{nome}' não encontrada.",
                ephemeral=True
            )
            return
        
        if persona.get("is_global") and not self.permission.is_admin(interaction.user, interaction.guild):
            await interaction.response.send_message(
                "❌ Apenas administradores podem remover personas globais.",
                ephemeral=True
            )
            return
        
        await self.db.delete_persona(nome, interaction.guild_id)
        
        await interaction.response.send_message(
            f"🗑️ Persona **{nome}** removida.",
            ephemeral=True
        )
    
    @persona_group.command(name="exportar", description="Exporta uma persona para JSON")
    @app_commands.describe(nome="Nome da persona")
    async def persona_export(
        self,
        interaction: discord.Interaction,
        nome: str
    ):
        """Exporta uma persona."""
        persona = await self.db.get_persona(nome, interaction.guild_id if interaction.guild else None)
        
        if not persona:
            await interaction.response.send_message(
                f"❌ Persona '{nome}' não encontrada.",
                ephemeral=True
            )
            return
        
        # Criar JSON
        export_data = {
            "name": persona["name"],
            "description": persona.get("description", ""),
            "system_prompt": persona.get("system_prompt", ""),
            "prompt_id": persona.get("prompt_id", ""),
            "version": "1.0"
        }
        
        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        # Enviar arquivo
        file = discord.File(
            fp=__import__('io').StringIO(json_str),
            filename=f"{nome}.persona.json"
        )
        
        await interaction.response.send_message(
            content=f"📦 Exportação da persona **{nome}**:",
            file=file,
            ephemeral=True
        )
    
    @persona_group.command(name="importar", description="Importa uma persona de um arquivo JSON")
    @app_commands.describe(arquivo="Arquivo JSON da persona")
    async def persona_import(
        self,
        interaction: discord.Interaction,
        arquivo: discord.Attachment
    ):
        """Importa uma persona."""
        if not self.permission.check_permissions(interaction, admin_only=True):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        # Verificar extensão
        if not arquivo.filename.endswith('.json'):
            await interaction.response.send_message(
                "❌ O arquivo deve ser um JSON.",
                ephemeral=True
            )
            return
        
        try:
            content = await arquivo.read()
            data = json.loads(content.decode('utf-8'))
            
            name = data.get("name", arquivo.filename.replace(".persona.json", "").replace(".json", ""))
            
            await self.db.create_persona(
                guild_id=interaction.guild_id,
                name=name,
                system_prompt=data.get("system_prompt", ""),
                prompt_id=data.get("prompt_id"),
                description=data.get("description"),
                created_by=interaction.user.id
            )
            
            await interaction.response.send_message(
                f"✅ Persona **{name}** importada com sucesso!",
                ephemeral=True
            )
            
        except json.JSONDecodeError:
            await interaction.response.send_message(
                "❌ Arquivo JSON inválido.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Erro ao importar: {e}",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(PersonaCommands(bot))
