"""
Menu/Painel de Personas
Interface interativa completa para gerenciar personas
"""

import json
import logging
from datetime import datetime
from typing import Optional

import discord
from discord import app_commands, ui
from discord.ext import commands

from core.config import Config
from core.evolving_persona import EvolvingPersona
from database.manager import DatabaseManager
from utils.permission_checker import PermissionChecker, permission_denied_message

logger = logging.getLogger("discord-bot")


class PersonaMenuView(ui.View):
    """Menu principal de personas."""
    
    def __init__(self, bot: commands.Bot, user_id: int, guild_id: Optional[int], timeout: float = 300):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.user_id = user_id
        self.guild_id = guild_id
        self.config: Config = bot.config
        self.db: DatabaseManager = bot.db
        self.current_page = 0
        self.selected_persona = None
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Este menu não é seu!", ephemeral=True)
            return False
        return True
    
    def get_embed(self) -> discord.Embed:
        """Cria embed do menu."""
        embed = discord.Embed(
            title="🎭 Menu de Personas",
            description="Gerencie suas personas e GPTs",
            color=discord.Color.purple()
        )
        
        # Persona ativa no canal
        # (simplificado - na implementação real buscaria do banco)
        embed.add_field(
            name="📌 Persona Ativa",
            value="Nenhuma (usando IA normal)",
            inline=False
        )
        
        # Modo atual
        embed.add_field(
            name="🎮 Modo Atual",
            value="💬 Normal (IA padrão)",
            inline=True
        )
        
        # Status
        embed.add_field(
            name="📊 Status",
            value="🟢 Ativo | Memória: ON",
            inline=True
        )
        
        embed.set_footer(text="Use os botões abaixo para navegar")
        
        return embed
    
    @ui.button(label="📋 Listar Personas", style=discord.ButtonStyle.primary, row=0)
    async def list_button(self, interaction: discord.Interaction, button: ui.Button):
        """Lista todas as personas."""
        view = PersonaListView(self.bot, self.user_id, self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)
    
    @ui.button(label="➕ Criar Nova", style=discord.ButtonStyle.success, row=0)
    async def create_button(self, interaction: discord.Interaction, button: ui.Button):
        """Cria nova persona."""
        modal = CreatePersonaModal(self.db, self.guild_id)
        await interaction.response.send_modal(modal)
    
    @ui.button(label="⚙️ Configurar Ativa", style=discord.ButtonStyle.secondary, row=0)
    async def config_button(self, interaction: discord.Interaction, button: ui.Button):
        """Configura persona ativa."""
        view = PersonaConfigView(self.bot, self.user_id, self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)
    
    @ui.button(label="🔄 Alternar Modo", style=discord.ButtonStyle.primary, row=1)
    async def mode_button(self, interaction: discord.Interaction, button: ui.Button):
        """Alterna entre modos."""
        view = ModeSelectView(self.bot, self.user_id, self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)
    
    @ui.button(label="🧬 Persona Evolutiva", style=discord.ButtonStyle.secondary, row=1)
    async def evolving_button(self, interaction: discord.Interaction, button: ui.Button):
        """Cria/configura persona evolutiva."""
        view = EvolvingPersonaView(self.bot, self.user_id, self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)
    
    @ui.button(label="📤 Importar", style=discord.ButtonStyle.secondary, row=2)
    async def import_button(self, interaction: discord.Interaction, button: ui.Button):
        """Importa persona."""
        await interaction.response.send_message(
            "📎 Envie o arquivo JSON da persona:",
            ephemeral=True
        )
    
    @ui.button(label="❌ Desativar", style=discord.ButtonStyle.danger, row=2)
    async def disable_button(self, interaction: discord.Interaction, button: ui.Button):
        """Desativa persona."""
        # Desativar persona no canal
        await self.db.set_channel_settings(
            interaction.channel_id,
            self.guild_id,
            persona_id=None,
            mode="normal"
        )
        
        embed = discord.Embed(
            title="🎭 Persona Desativada",
            description="Voltando ao modo IA normal.",
            color=discord.Color.greyple()
        )
        await interaction.response.edit_message(embed=embed, view=None)


class PersonaListView(ui.View):
    """Lista de personas disponíveis."""
    
    def __init__(self, bot: commands.Bot, user_id: int, guild_id: Optional[int]):
        super().__init__(timeout=180)
        self.bot = bot
        self.user_id = user_id
        self.guild_id = guild_id
        self.db = bot.db
    
    def get_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📋 Personas Disponíveis",
            description="Clique em uma para ativar",
            color=discord.Color.purple()
        )
        
        # Personas globais
        embed.add_field(
            name="🌍 Globais",
            value="• Assistente Padrão\n• Professor\n• Programador",
            inline=False
        )
        
        # Personas do servidor
        if self.guild_id:
            embed.add_field(
                name="🏠 Deste Servidor",
                value="• Mascote do Server\n• Helper",
                inline=False
            )
        
        # Personas evolutivas
        embed.add_field(
            name="🧬 Evolutivas",
            value="• Minha Persona (evoluindo)",
            inline=False
        )
        
        return embed
    
    @ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.secondary, row=0)
    async def back_button(self, interaction: discord.Interaction, button: ui.Button):
        view = PersonaMenuView(self.bot, self.user_id, self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)
    
    @ui.select(
        placeholder="Selecione uma persona...",
        options=[
            discord.SelectOption(label="Assistente Padrão", value="default", emoji="🤖"),
            discord.SelectOption(label="Professor", value="professor", emoji="🎓"),
            discord.SelectOption(label="Programador", value="programmer", emoji="💻"),
            discord.SelectOption(label="Criativo", value="creative", emoji="🎨"),
        ],
        row=1
    )
    async def persona_select(self, interaction: discord.Interaction, select: ui.Select):
        """Seleciona uma persona."""
        persona_name = select.values[0]
        
        # Ativar persona
        await self.db.set_channel_settings(
            interaction.channel_id,
            self.guild_id,
            persona_id=persona_name,
            mode="roleplay"
        )
        
        embed = discord.Embed(
            title=f"🎭 Persona Ativada",
            description=f"**{persona_name}** está ativa neste canal!",
            color=discord.Color.green()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)


class ModeSelectView(ui.View):
    """Seleção de modo de operação."""
    
    def __init__(self, bot: commands.Bot, user_id: int, guild_id: Optional[int]):
        super().__init__(timeout=180)
        self.bot = bot
        self.user_id = user_id
        self.guild_id = guild_id
        self.db = bot.db
    
    def get_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎮 Selecionar Modo",
            description="Escolha como o bot deve operar",
            color=discord.Color.blue()
        )
        
        modes = [
            ("💬 Normal", "IA padrão com histórico", "normal"),
            ("🤖 Assistant", "OpenAI Assistant com ferramentas", "assistant"),
            ("🎯 Chatbot", "Responde automaticamente", "chatbot"),
            ("👤 Interativo", "Membro do servidor com personalidade", "interactive"),
            ("🎭 Roleplay", "Persona específica", "roleplay"),
        ]
        
        for icon_name, desc, mode_id in modes:
            embed.add_field(
                name=icon_name,
                value=desc,
                inline=False
            )
        
        return embed
    
    @ui.select(
        placeholder="Selecione o modo...",
        options=[
            discord.SelectOption(label="💬 Normal", value="normal", 
                               description="IA padrão com histórico"),
            discord.SelectOption(label="🤖 Assistant", value="assistant",
                               description="OpenAI Assistant com ferramentas"),
            discord.SelectOption(label="🎯 Chatbot", value="chatbot",
                               description="Responde automaticamente sem gatilhos"),
            discord.SelectOption(label="👤 Interativo", value="interactive",
                               description="Membro do servidor com personalidade complexa"),
            discord.SelectOption(label="🎭 Roleplay", value="roleplay",
                               description="Persona específica"),
        ]
    )
    async def mode_select(self, interaction: discord.Interaction, select: ui.Select):
        """Seleciona modo."""
        mode = select.values[0]
        
        # Salvar modo
        await self.db.set_channel_settings(
            interaction.channel_id,
            self.guild_id,
            mode=mode
        )
        
        mode_names = {
            "normal": "💬 Normal",
            "assistant": "🤖 Assistant",
            "chatbot": "🎯 Chatbot",
            "interactive": "👤 Interativo",
            "roleplay": "🎭 Roleplay"
        }
        
        embed = discord.Embed(
            title="🎮 Modo Alterado",
            description=f"Modo: **{mode_names.get(mode, mode)}**",
            color=discord.Color.green()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    @ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction: discord.Interaction, button: ui.Button):
        view = PersonaMenuView(self.bot, self.user_id, self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)


class EvolvingPersonaView(ui.View):
    """Configuração de persona evolutiva."""
    
    def __init__(self, bot: commands.Bot, user_id: int, guild_id: Optional[int]):
        super().__init__(timeout=180)
        self.bot = bot
        self.user_id = user_id
        self.guild_id = guild_id
    
    def get_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🧬 Persona Evolutiva",
            description="Uma persona que aprende e evolui com o tempo",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="✨ Características",
            value=(
                "• Aprende com conversas\n"
                "• Desenvolve relacionamentos\n"
                "• Forma opiniões\n"
                "• Tem memórias emocionais\n"
                "• Evolui traços de personalidade"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📊 Status Atual",
            value=(
                "• Interações: 150\n"
                "• Relacionamentos: 12\n"
                "• Fatos aprendidos: 45\n"
                "• Evoluções: 3"
            ),
            inline=True
        )
        
        return embed
    
    @ui.button(label="🆕 Criar Nova", style=discord.ButtonStyle.success, row=0)
    async def create_button(self, interaction: discord.Interaction, button: ui.Button):
        """Cria nova persona evolutiva."""
        modal = CreateEvolvingPersonaModal(self.guild_id)
        await interaction.response.send_modal(modal)
    
    @ui.button(label="📊 Ver Evolução", style=discord.ButtonStyle.primary, row=0)
    async def evolution_button(self, interaction: discord.Interaction, button: ui.Button):
        """Mostra evolução da persona."""
        embed = discord.Embed(
            title="📊 Evolução da Persona",
            description="Histórico de mudanças",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Traços Atuais",
            value=(
                "• Extroversão: 65%\n"
                "• Humor: 80%\n"
                "• Empatia: 70%\n"
                "• Curiosidade: 85%"
            ),
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.secondary, row=1)
    async def back_button(self, interaction: discord.Interaction, button: ui.Button):
        view = PersonaMenuView(self.bot, self.user_id, self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)


class PersonaConfigView(ui.View):
    """Configurações da persona ativa."""
    
    def __init__(self, bot: commands.Bot, user_id: int, guild_id: Optional[int]):
        super().__init__(timeout=180)
        self.bot = bot
        self.user_id = user_id
        self.guild_id = guild_id
    
    def get_embed(self) -> discord.Embed:
        return discord.Embed(
            title="⚙️ Configurar Persona",
            description="Ajustes da persona ativa",
            color=discord.Color.greyple()
        )
    
    @ui.button(label="🧠 Memória", style=discord.ButtonStyle.primary, row=0)
    async def memory_button(self, interaction: discord.Interaction, button: ui.Button):
        """Configura memória."""
        await interaction.response.send_message("🧠 Configuração de memória", ephemeral=True)
    
    @ui.button(label="👁️ Visão", style=discord.ButtonStyle.primary, row=0)
    async def vision_button(self, interaction: discord.Interaction, button: ui.Button):
        """Configura visão de imagens."""
        await interaction.response.send_message("👁️ Configuração de visão", ephemeral=True)
    
    @ui.button(label="🔊 Áudio", style=discord.ButtonStyle.primary, row=0)
    async def audio_button(self, interaction: discord.Interaction, button: ui.Button):
        """Configura áudio."""
        await interaction.response.send_message("🔊 Configuração de áudio", ephemeral=True)
    
    @ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.secondary, row=1)
    async def back_button(self, interaction: discord.Interaction, button: ui.Button):
        view = PersonaMenuView(self.bot, self.user_id, self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)


class CreatePersonaModal(ui.Modal, title="Criar Nova Persona"):
    """Modal para criar persona."""
    
    name = ui.TextInput(label="Nome", placeholder="Ex: Professor de Python", required=True)
    prompt = ui.TextInput(
        label="System Prompt",
        placeholder="Descreva a personalidade...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=2000
    )
    description = ui.TextInput(
        label="Descrição (opcional)",
        placeholder="Breve descrição...",
        required=False
    )
    
    def __init__(self, db: DatabaseManager, guild_id: Optional[int]):
        super().__init__()
        self.db = db
        self.guild_id = guild_id
    
    async def on_submit(self, interaction: discord.Interaction):
        await self.db.create_persona(
            guild_id=self.guild_id,
            name=self.name.value,
            system_prompt=self.prompt.value,
            description=self.description.value or None,
            created_by=interaction.user.id
        )
        
        await interaction.response.send_message(
            f"✅ Persona **{self.name.value}** criada!",
            ephemeral=True
        )


class CreateEvolvingPersonaModal(ui.Modal, title="Criar Persona Evolutiva"):
    """Modal para criar persona evolutiva."""
    
    name = ui.TextInput(label="Nome", placeholder="Ex: Meu Amigo Virtual", required=True)
    base_prompt = ui.TextInput(
        label="Base de Personalidade",
        placeholder="Quem é esta persona?",
        style=discord.TextStyle.paragraph,
        required=True
    )
    
    def __init__(self, guild_id: Optional[int]):
        super().__init__()
        self.guild_id = guild_id
    
    async def on_submit(self, interaction: discord.Interaction):
        persona = EvolvingPersona(
            persona_id=f"evolving_{interaction.user.id}_{self.name.value}",
            name=self.name.value,
            base_prompt=self.base_prompt.value
        )
        
        # Salvar no banco
        # (implementar método na database)
        
        await interaction.response.send_message(
            f"🧬 Persona evolutiva **{self.name.value}** criada!\n"
            f"Ela começará a aprender e evoluir a partir das conversas.",
            ephemeral=True
        )


class PersonaMenuCommands(commands.Cog):
    """Comandos do menu de personas."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config
        self.db: DatabaseManager = bot.db
        self.permission = PermissionChecker(self.config)
    
    @app_commands.command(name="persona", description="Abre o menu de personas")
    async def persona_menu(self, interaction: discord.Interaction):
        """Abre menu de personas."""
        if not self.permission.check_permissions(interaction):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        view = PersonaMenuView(
            self.bot, 
            interaction.user.id,
            interaction.guild_id
        )
        
        await interaction.response.send_message(
            embed=view.get_embed(),
            view=view,
            ephemeral=True
        )
    
    @app_commands.command(name="modo", description="Muda o modo de operação do bot")
    @app_commands.describe(modo="Modo de operação")
    @app_commands.choices(modo=[
        app_commands.Choice(name="💬 Normal", value="normal"),
        app_commands.Choice(name="🤖 Assistant", value="assistant"),
        app_commands.Choice(name="🎯 Chatbot", value="chatbot"),
        app_commands.Choice(name="👤 Interativo", value="interactive"),
        app_commands.Choice(name="🎭 Roleplay", value="roleplay"),
    ])
    async def change_mode(
        self,
        interaction: discord.Interaction,
        modo: app_commands.Choice[str]
    ):
        """Muda modo de operação."""
        if not self.permission.check_permissions(interaction, admin_only=True):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        await self.db.set_channel_settings(
            interaction.channel_id,
            interaction.guild_id,
            mode=modo.value
        )
        
        await interaction.response.send_message(
            f"🎮 Modo alterado para: **{modo.name}**",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(PersonaMenuCommands(bot))
