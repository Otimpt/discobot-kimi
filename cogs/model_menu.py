"""
Painel/Menu de Modelos
Interface interativa para selecionar e configurar modelos
"""

import logging
from typing import Optional, List

import discord
from discord import app_commands, ui
from discord.ext import commands

from core.config import Config
from database.manager import DatabaseManager
from providers.manager import ProviderManager
from utils.permission_checker import PermissionChecker, permission_denied_message

logger = logging.getLogger("discord-bot")


class ModelMenuView(ui.View):
    """Menu interativo de modelos."""
    
    def __init__(self, bot: commands.Bot, user_id: int, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.user_id = user_id
        self.config: Config = bot.config
        self.provider: ProviderManager = bot.provider
        self.db: DatabaseManager = bot.db
        self.current_page = 0
        self.selected_provider = None
        self.models_per_page = 5
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Verifica se o usuário pode usar o menu."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Este menu não é seu! Use `/modelo menu` para abrir o seu.",
                ephemeral=True
            )
            return False
        return True
    
    def get_embed(self) -> discord.Embed:
        """Cria o embed do menu."""
        embed = discord.Embed(
            title="🧠 Menu de Modelos",
            description="Selecione um modelo para usar neste canal",
            color=discord.Color.blue()
        )
        
        # Modelo atual
        settings = self.db.get_channel_settings_sync(self.user_id)  # Simplified
        current = settings.get("model") if settings else None
        current = current or self.config.default_model
        
        embed.add_field(
            name="📌 Modelo Atual",
            value=f"**{current}**",
            inline=False
        )
        
        # Lista de modelos
        models = self.provider.list_available_models()
        
        if self.selected_provider:
            models = [m for m in models if m["provider"] == self.selected_provider]
        
        # Paginação
        start = self.current_page * self.models_per_page
        end = start + self.models_per_page
        page_models = models[start:end]
        
        if page_models:
            models_text = ""
            for i, model in enumerate(page_models, start + 1):
                status = "🟢" if model["enabled"] else "🔴"
                vision = " 👁️" if model["vision_capable"] else ""
                tools = " 🔧" if model["supports_tools"] else ""
                current_marker = " ⭐" if f"{model['provider']}/{model['name']}" == current else ""
                
                models_text += f"{status} **{i}.** {model['name']}{vision}{tools}{current_marker}\n"
                models_text += f"   └ Provedor: {model['provider']} | ID: `{model['model_id']}`\n\n"
            
            embed.add_field(
                name=f"📋 Modelos (Página {self.current_page + 1}/{(len(models) // self.models_per_page) + 1})",
                value=models_text or "Nenhum modelo encontrado",
                inline=False
            )
        
        # Info
        embed.add_field(
            name="ℹ️ Legenda",
            value="👁️ = Vision | 🔧 = Tools | ⭐ = Atual | 🟢 = Disponível | 🔴 = Indisponível",
            inline=False
        )
        
        embed.set_footer(text="Use os botões abaixo para navegar e selecionar")
        
        return embed
    
    @ui.button(label="◀️ Anterior", style=discord.ButtonStyle.secondary, row=0)
    async def prev_button(self, interaction: discord.Interaction, button: ui.Button):
        """Página anterior."""
        if self.current_page > 0:
            self.current_page -= 1
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    @ui.button(label="▶️ Próxima", style=discord.ButtonStyle.secondary, row=0)
    async def next_button(self, interaction: discord.Interaction, button: ui.Button):
        """Próxima página."""
        models = self.provider.list_available_models()
        max_page = (len(models) // self.models_per_page)
        
        if self.current_page < max_page:
            self.current_page += 1
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
    
    @ui.button(label="🔍 Filtrar", style=discord.ButtonStyle.primary, row=0)
    async def filter_button(self, interaction: discord.Interaction, button: ui.Button):
        """Abre menu de filtros."""
        # Criar select para provedores
        providers = list(set(m["provider"] for m in self.provider.list_available_models()))
        
        options = [discord.SelectOption(label="Todos", value="all", description="Mostrar todos os modelos")]
        for provider in providers:
            options.append(discord.SelectOption(
                label=provider.capitalize(),
                value=provider,
                description=f"Filtrar por {provider}"
            ))
        
        select = ui.Select(placeholder="Filtrar por provedor...", options=options)
        
        async def select_callback(select_interaction: discord.Interaction):
            value = select.values[0]
            self.selected_provider = None if value == "all" else value
            self.current_page = 0
            await select_interaction.response.edit_message(embed=self.get_embed(), view=self)
        
        select.callback = select_callback
        
        view = ui.View()
        view.add_item(select)
        view.add_item(ui.Button(label="Voltar", style=discord.ButtonStyle.secondary, custom_id="back"))
        
        await interaction.response.send_message("Selecione um provedor:", view=view, ephemeral=True)
    
    @ui.button(label="⚙️ Configurar", style=discord.ButtonStyle.primary, row=1)
    async def config_button(self, interaction: discord.Interaction, button: ui.Button):
        """Abre configurações do modelo atual."""
        settings = await self.db.get_channel_settings(interaction.channel_id)
        current = settings.get("model") if settings else self.config.default_model
        
        model_config = self.config.get_model(current.split("/")[-1]) if "/" in current else self.config.get_model(current)
        
        if not model_config:
            await interaction.response.send_message(
                "❌ Não foi possível obter configurações do modelo atual.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f"⚙️ Configurações: {current}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Temperatura", value=str(model_config.temperature), inline=True)
        embed.add_field(name="Max Tokens", value=str(model_config.max_tokens), inline=True)
        embed.add_field(name="Vision", value="✅" if model_config.vision_capable else "❌", inline=True)
        embed.add_field(name="Tools", value="✅" if model_config.supports_tools else "❌", inline=True)
        
        # Botões para ajustar
        view = ui.View()
        
        # Temperature buttons
        temp_down = ui.Button(label="🌡️ -0.1", style=discord.ButtonStyle.secondary)
        temp_up = ui.Button(label="🌡️ +0.1", style=discord.ButtonStyle.secondary)
        
        async def temp_callback(temp_interaction: discord.Interaction, delta: float):
            new_temp = max(0.0, min(2.0, model_config.temperature + delta))
            # Atualizar no banco (simplificado)
            await temp_interaction.response.send_message(
                f"🌡️ Temperatura ajustada para {new_temp:.1f}",
                ephemeral=True
            )
        
        temp_down.callback = lambda i: temp_callback(i, -0.1)
        temp_up.callback = lambda i: temp_callback(i, 0.1)
        
        view.add_item(temp_down)
        view.add_item(temp_up)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @ui.button(label="✅ Usar Este", style=discord.ButtonStyle.success, row=1)
    async def use_button(self, interaction: discord.Interaction, button: ui.Button):
        """Usar modelo selecionado."""
        # Abrir modal para digitar nome do modelo
        modal = ModelSelectModal(self.db, self.config)
        await interaction.response.send_modal(modal)
    
    @ui.button(label="➕ Adicionar", style=discord.ButtonStyle.success, row=2)
    async def add_button(self, interaction: discord.Interaction, button: ui.Button):
        """Adicionar modelo customizado."""
        modal = AddModelModal(self.db, self.config)
        await interaction.response.send_modal(modal)
    
    @ui.button(label="🗑️ Remover", style=discord.ButtonStyle.danger, row=2)
    async def remove_button(self, interaction: discord.Interaction, button: ui.Button):
        """Remover modelo customizado."""
        # Listar modelos customizados
        custom_models = await self.db.list_custom_models()
        
        if not custom_models:
            await interaction.response.send_message(
                "📭 Não há modelos customizados para remover.",
                ephemeral=True
            )
            return
        
        options = [
            discord.SelectOption(label=m["name"], value=m["name"], description=f"{m['provider']}/{m['model_id']}")
            for m in custom_models
        ]
        
        select = ui.Select(placeholder="Selecione um modelo para remover...", options=options)
        
        async def remove_callback(remove_interaction: discord.Interaction):
            model_name = select.values[0]
            await self.db.delete_custom_model(model_name)
            self.config.remove_model(model_name)
            
            await remove_interaction.response.send_message(
                f"🗑️ Modelo **{model_name}** removido.",
                ephemeral=True
            )
        
        select.callback = remove_callback
        
        view = ui.View()
        view.add_item(select)
        
        await interaction.response.send_message("Selecione o modelo para remover:", view=view, ephemeral=True)


class ModelSelectModal(ui.Modal, title="Selecionar Modelo"):
    """Modal para selecionar modelo por nome."""
    
    model_name = ui.TextInput(
        label="Nome do Modelo",
        placeholder="Ex: gpt-4o, claude-sonnet-4, llama-3.3-70b",
        required=True
    )
    
    def __init__(self, db: DatabaseManager, config: Config):
        super().__init__()
        self.db = db
        self.config = config
    
    async def on_submit(self, interaction: discord.Interaction):
        """Processa seleção."""
        model_name = self.model_name.value.strip()
        
        # Verificar se modelo existe
        model_config = self.config.get_model(model_name)
        
        if not model_config:
            # Tentar com provedor
            for provider in self.config.providers.keys():
                full_name = f"{provider}/{model_name}"
                model_config = self.config.get_model(full_name)
                if model_config:
                    model_name = full_name
                    break
        
        if not model_config:
            await interaction.response.send_message(
                f"❌ Modelo '{model_name}' não encontrado.\n"
                f"Use `/modelo listar` para ver os disponíveis.",
                ephemeral=True
            )
            return
        
        # Verificar se provedor está habilitado
        provider = self.config.get_provider(model_config.provider)
        if not provider or not provider.enabled:
            await interaction.response.send_message(
                f"❌ Provedor '{model_config.provider}' não está habilitado.\n"
                f"Verifique suas configurações.",
                ephemeral=True
            )
            return
        
        # Salvar configuração
        await self.db.set_channel_settings(
            interaction.channel_id,
            interaction.guild_id,
            model=model_name
        )
        
        embed = discord.Embed(
            title="✅ Modelo Alterado",
            description=f"Modelo definido: **{model_name}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Provedor", value=model_config.provider, inline=True)
        embed.add_field(name="ID", value=model_config.model_id, inline=True)
        
        if model_config.vision_capable:
            embed.add_field(name="Recursos", value="👁️ Vision API", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


class AddModelModal(ui.Modal, title="Adicionar Modelo Customizado"):
    """Modal para adicionar modelo."""
    
    name = ui.TextInput(
        label="Nome do Modelo",
        placeholder="Ex: meu-llama-local",
        required=True
    )
    
    provider = ui.TextInput(
        label="Provedor",
        placeholder="Ex: openai, ollama, lmstudio",
        required=True
    )
    
    model_id = ui.TextInput(
        label="ID do Modelo na API",
        placeholder="Ex: llama3, gpt-4o, etc",
        required=True
    )
    
    temperature = ui.TextInput(
        label="Temperatura (0.0 - 2.0)",
        placeholder="0.9",
        default="0.9",
        required=False
    )
    
    def __init__(self, db: DatabaseManager, config: Config):
        super().__init__()
        self.db = db
        self.config = config
    
    async def on_submit(self, interaction: discord.Interaction):
        """Processa adição."""
        try:
            temp = float(self.temperature.value or "0.9")
        except ValueError:
            temp = 0.9
        
        # Verificar se provedor existe
        provider = self.config.get_provider(self.provider.value)
        if not provider:
            available = ", ".join(self.config.providers.keys())
            await interaction.response.send_message(
                f"❌ Provedor '{self.provider.value}' não encontrado.\n"
                f"Disponíveis: {available}",
                ephemeral=True
            )
            return
        
        # Adicionar
        await self.db.add_custom_model(
            name=self.name.value,
            provider=self.provider.value,
            model_id=self.model_id.value,
            temperature=temp,
            created_by=interaction.user.id
        )
        
        self.config.add_model(self.name.value, {
            "provider": self.provider.value,
            "model_id": self.model_id.value,
            "temperature": temp
        })
        
        await interaction.response.send_message(
            f"✅ Modelo **{self.name.value}** adicionado!\n"
            f"Provedor: {self.provider.value}\n"
            f"ID: {self.model_id.value}",
            ephemeral=True
        )


class ModelMenuCommands(commands.Cog):
    """Comandos do menu de modelos."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config
        self.db: DatabaseManager = bot.db
        self.provider: ProviderManager = bot.provider
        self.permission = PermissionChecker(self.config)
    
    @app_commands.command(name="modelo", description="Abre o menu de modelos")
    async def modelo_menu(self, interaction: discord.Interaction):
        """Abre menu interativo de modelos."""
        if not self.permission.check_permissions(interaction):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        view = ModelMenuView(self.bot, interaction.user.id)
        await interaction.response.send_message(embed=view.get_embed(), view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(ModelMenuCommands(bot))
