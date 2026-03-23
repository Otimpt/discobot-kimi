"""
Comandos de Modelos
Gerenciamento de modelos LLM disponíveis
"""

import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from core.config import Config
from database.manager import DatabaseManager
from providers.manager import ProviderManager
from utils.permission_checker import PermissionChecker, permission_denied_message

logger = logging.getLogger("discord-bot")


class ModelCommands(commands.Cog):
    """Comandos para gerenciar modelos LLM."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config
        self.db: DatabaseManager = bot.db
        self.provider: ProviderManager = bot.provider
        self.permission = PermissionChecker(self.config)
    
    modelo_group = app_commands.Group(
        name="modelo",
        description="Gerenciamento de modelos LLM"
    )
    
    @modelo_group.command(name="listar", description="Lista todos os modelos disponíveis")
    async def model_list(self, interaction: discord.Interaction):
        """Lista modelos disponíveis."""
        models = self.provider.list_available_models()
        
        if not models:
            await interaction.response.send_message(
                "❌ Nenhum modelo disponível.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🧠 Modelos Disponíveis",
            description="Use `/modelo usar <nome>` para selecionar um modelo",
            color=discord.Color.blue()
        )
        
        enabled_models = [m for m in models if m["enabled"]]
        disabled_models = [m for m in models if not m["enabled"]]
        
        if enabled_models:
            enabled_text = "\n".join([
                f"• **{m['name']}** ({m['provider']})"
                f"{' 👁️' if m['vision_capable'] else ''}"
                f"{' 🔧' if m['supports_tools'] else ''}"
                for m in enabled_models[:15]
            ])
            embed.add_field(
                name="✅ Disponíveis",
                value=enabled_text or "Nenhum",
                inline=False
            )
        
        if disabled_models:
            disabled_text = "\n".join([
                f"• {m['name']} ({m['provider']})"
                for m in disabled_models[:5]
            ])
            embed.add_field(
                name="❌ Provedor não configurado",
                value=disabled_text + "\n..." if len(disabled_models) > 5 else disabled_text,
                inline=False
            )
        
        # Mostrar modelo atual do canal
        settings = await self.db.get_channel_settings(interaction.channel_id)
        current_model = settings.get("model") or self.config.default_model
        embed.set_footer(text=f"Modelo atual: {current_model}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @modelo_group.command(name="usar", description="Define o modelo para este canal")
    @app_commands.describe(
        modelo="Nome do modelo a usar"
    )
    @app_commands.autocomplete(modelo=lambda interaction, current: [
        app_commands.Choice(name=m["name"], value=m["name"])
        for m in interaction.client.provider.list_available_models()
        if m["enabled"] and current.lower() in m["name"].lower()
    ][:25])
    async def model_use(
        self,
        interaction: discord.Interaction,
        modelo: str
    ):
        """Define o modelo do canal."""
        if not self.permission.check_permissions(interaction, admin_only=True):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        # Verificar se modelo existe
        model_config = self.config.get_model(modelo)
        if not model_config:
            await interaction.response.send_message(
                f"❌ Modelo '{modelo}' não encontrado.",
                ephemeral=True
            )
            return
        
        # Verificar se provedor está habilitado
        provider = self.config.get_provider(model_config.provider)
        if not provider or not provider.enabled:
            await interaction.response.send_message(
                f"❌ Provedor '{model_config.provider}' não está configurado.",
                ephemeral=True
            )
            return
        
        # Salvar configuração
        await self.db.set_channel_settings(
            interaction.channel_id,
            interaction.guild_id,
            model=modelo
        )
        
        embed = discord.Embed(
            title="🧠 Modelo Alterado",
            description=f"Modelo definido: **{modelo}**",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Provedor",
            value=model_config.provider,
            inline=True
        )
        embed.add_field(
            name="ID do Modelo",
            value=model_config.model_id,
            inline=True
        )
        
        if model_config.vision_capable:
            embed.add_field(
                name="Recursos",
                value="👁️ Vision API",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @modelo_group.command(name="adicionar", description="Adiciona um modelo customizado")
    @app_commands.describe(
        nome="Nome do modelo",
        provedor="Provedor do modelo",
        model_id="ID do modelo na API",
        temperatura="Temperatura (0.0 - 2.0)",
        max_tokens="Máximo de tokens"
    )
    async def model_add(
        self,
        interaction: discord.Interaction,
        nome: str,
        provedor: str,
        model_id: str,
        temperatura: Optional[float] = 0.9,
        max_tokens: Optional[int] = 4096
    ):
        """Adiciona um modelo customizado."""
        if not self.permission.check_permissions(interaction, admin_only=True):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        # Verificar se provedor existe
        provider = self.config.get_provider(provedor)
        if not provider:
            available = ", ".join(self.config.providers.keys())
            await interaction.response.send_message(
                f"❌ Provedor '{provedor}' não encontrado.\n"
                f"Provedores disponíveis: {available}",
                ephemeral=True
            )
            return
        
        # Adicionar ao banco de dados
        await self.db.add_custom_model(
            name=nome,
            provider=provedor,
            model_id=model_id,
            temperature=temperatura,
            max_tokens=max_tokens,
            created_by=interaction.user.id
        )
        
        # Adicionar à configuração em memória
        self.config.add_model(nome, {
            "provider": provedor,
            "model_id": model_id,
            "temperature": temperatura,
            "max_tokens": max_tokens
        })
        
        embed = discord.Embed(
            title="✅ Modelo Adicionado",
            description=f"Modelo **{nome}** adicionado com sucesso!",
            color=discord.Color.green()
        )
        embed.add_field(name="Provedor", value=provedor, inline=True)
        embed.add_field(name="Model ID", value=model_id, inline=True)
        embed.add_field(name="Temperatura", value=str(temperatura), inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @modelo_group.command(name="remover", description="Remove um modelo customizado")
    @app_commands.describe(nome="Nome do modelo a remover")
    @app_commands.autocomplete(nome=lambda interaction, current: [
        app_commands.Choice(name=m["name"], value=m["name"])
        for m in interaction.client.db.list_custom_models()
        if current.lower() in m["name"].lower()
    ][:25])
    async def model_remove(
        self,
        interaction: discord.Interaction,
        nome: str
    ):
        """Remove um modelo customizado."""
        if not self.permission.check_permissions(interaction, admin_only=True):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        # Verificar se é um modelo customizado
        custom_model = await self.db.get_custom_model(nome)
        if not custom_model:
            await interaction.response.send_message(
                f"❌ Modelo '{nome}' não encontrado ou não é customizado.",
                ephemeral=True
            )
            return
        
        # Remover
        await self.db.delete_custom_model(nome)
        self.config.remove_model(nome)
        
        await interaction.response.send_message(
            f"✅ Modelo **{nome}** removido com sucesso!",
            ephemeral=True
        )
    
    @modelo_group.command(name="info", description="Mostra informações sobre um modelo")
    @app_commands.describe(nome="Nome do modelo")
    async def model_info(
        self,
        interaction: discord.Interaction,
        nome: str
    ):
        """Mostra informações de um modelo."""
        model_config = self.config.get_model(nome)
        
        if not model_config:
            await interaction.response.send_message(
                f"❌ Modelo '{nome}' não encontrado.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f"🧠 {nome}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Provedor", value=model_config.provider, inline=True)
        embed.add_field(name="Model ID", value=model_config.model_id, inline=True)
        embed.add_field(name="Temperatura", value=str(model_config.temperature), inline=True)
        embed.add_field(name="Max Tokens", value=str(model_config.max_tokens), inline=True)
        embed.add_field(name="Vision", value="✅" if model_config.vision_capable else "❌", inline=True)
        embed.add_field(name="Tools", value="✅" if model_config.supports_tools else "❌", inline=True)
        
        # Custo estimado
        if model_config.cost_per_1k_input > 0:
            cost_text = f"${model_config.cost_per_1k_input}/1K input\n${model_config.cost_per_1k_output}/1K output"
            embed.add_field(name="Custo Estimado", value=cost_text, inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @modelo_group.command(name="padrao", description="Define o modelo padrão do servidor")
    @app_commands.describe(modelo="Nome do modelo")
    async def model_default(
        self,
        interaction: discord.Interaction,
        modelo: str
    ):
        """Define o modelo padrão do servidor."""
        if not self.permission.check_permissions(interaction, admin_only=True):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        model_config = self.config.get_model(modelo)
        if not model_config:
            await interaction.response.send_message(
                f"❌ Modelo '{modelo}' não encontrado.",
                ephemeral=True
            )
            return
        
        # Atualizar configuração do servidor
        await self.db.update_guild_config(
            interaction.guild_id,
            default_model=modelo
        )
        
        await interaction.response.send_message(
            f"✅ Modelo padrão do servidor definido: **{modelo}**",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(ModelCommands(bot))
