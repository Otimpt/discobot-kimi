"""
Comandos de Configuração
Painel de configuração interativo e comandos de setup
"""

import logging
from typing import Optional

import discord
from discord import app_commands, ui
from discord.ext import commands

from core.config import Config
from database.manager import DatabaseManager
from utils.permission_checker import PermissionChecker, permission_denied_message

logger = logging.getLogger("discord-bot")


class ConfigView(ui.View):
    """View interativa do painel de configuração."""
    
    def __init__(self, channel_id: int, db: DatabaseManager, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.channel_id = channel_id
        self.db = db
        self.settings = {}
    
    async def refresh(self):
        """Atualiza as configurações do canal."""
        self.settings = await self.db.get_channel_settings(self.channel_id)
    
    def create_embed(self) -> discord.Embed:
        """Cria o embed do painel."""
        mode_map = {
            0: "🔴 Desativado",
            1: "🟢 Inteligente",
            3: "💧 Fluido",
            4: "⚡ Frenético",
            5: "🎭 Roleplay"
        }
        
        trigger_map = {
            "standard": "👋 Menção/Reply",
            "prefix": "❗ Prefixo (!)",
            "all": "🌐 Todos",
            "off": "🔕 Desativado"
        }
        
        safety_map = {
            "none": "🚫 Nenhum",
            "low": "🟢 Baixo",
            "medium": "🟡 Médio",
            "standard": "🔵 Padrão",
            "high": "🟠 Alto",
            "strict": "🔴 Estrito"
        }
        
        mode = self.settings.get("chatbot_mode", 1)
        trigger = self.settings.get("trigger_mode", "standard")
        safety = self.settings.get("safety_mode", "standard")
        is_active = self.settings.get("is_active", False)
        
        embed = discord.Embed(
            title="⚙️ Painel de Configuração",
            description=f"Configurações do canal <#{self.channel_id}>",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Status",
            value="🟢 Ativo" if is_active else "🔴 Inativo",
            inline=True
        )
        embed.add_field(
            name="Modo Chatbot",
            value=mode_map.get(mode, "Desconhecido"),
            inline=True
        )
        embed.add_field(
            name="Gatilhos",
            value=trigger_map.get(trigger, "Desconhecido"),
            inline=True
        )
        embed.add_field(
            name="Segurança",
            value=safety_map.get(safety, "Desconhecido"),
            inline=True
        )
        embed.add_field(
            name="Memória",
            value="🟢 Ativa" if self.settings.get("use_memory", True) else "🔴 Desativada",
            inline=True
        )
        embed.add_field(
            name="Contexto Isolado",
            value="🟢 Sim" if self.settings.get("isolated_context", False) else "🔴 Não",
            inline=True
        )
        
        if self.settings.get("model"):
            embed.add_field(
                name="Modelo",
                value=self.settings.get("model"),
                inline=True
            )
        
        if self.settings.get("persona_id"):
            embed.add_field(
                name="Persona Ativa",
                value=self.settings.get("persona_id"),
                inline=True
            )
        
        embed.set_footer(text="Use os botões abaixo para configurar")
        
        return embed
    
    @ui.button(label="Ativar/Desativar", style=discord.ButtonStyle.primary, row=0)
    async def toggle_button(self, interaction: discord.Interaction, button: ui.Button):
        """Ativa/desativa o bot no canal."""
        new_state = not self.settings.get("is_active", False)
        await self.db.set_channel_active(self.channel_id, new_state)
        await self.refresh()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)
    
    @ui.select(
        placeholder="Modo Chatbot",
        options=[
            discord.SelectOption(label="Desativado", value="0", emoji="🔴"),
            discord.SelectOption(label="Inteligente", value="1", emoji="🟢"),
            discord.SelectOption(label="Fluido", value="3", emoji="💧"),
            discord.SelectOption(label="Frenético", value="4", emoji="⚡"),
            discord.SelectOption(label="Roleplay", value="5", emoji="🎭"),
        ],
        row=1
    )
    async def mode_select(self, interaction: discord.Interaction, select: ui.Select):
        """Altera o modo do chatbot."""
        await self.db.set_channel_settings(
            self.channel_id,
            None,
            chatbot_mode=int(select.values[0])
        )
        await self.refresh()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)
    
    @ui.select(
        placeholder="Gatilhos",
        options=[
            discord.SelectOption(label="Menção/Reply", value="standard", emoji="👋"),
            discord.SelectOption(label="Prefixo (!)", value="prefix", emoji="❗"),
            discord.SelectOption(label="Todos", value="all", emoji="🌐"),
            discord.SelectOption(label="Desativado", value="off", emoji="🔕"),
        ],
        row=2
    )
    async def trigger_select(self, interaction: discord.Interaction, select: ui.Select):
        """Altera o modo de gatilhos."""
        await self.db.set_channel_settings(
            self.channel_id,
            None,
            trigger_mode=select.values[0]
        )
        await self.refresh()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)
    
    @ui.select(
        placeholder="Nível de Segurança",
        options=[
            discord.SelectOption(label="Sem Filtro", value="none", emoji="🚫"),
            discord.SelectOption(label="Baixo", value="low", emoji="🟢"),
            discord.SelectOption(label="Médio", value="medium", emoji="🟡"),
            discord.SelectOption(label="Padrão", value="standard", emoji="🔵"),
            discord.SelectOption(label="Alto", value="high", emoji="🟠"),
            discord.SelectOption(label="Estrito", value="strict", emoji="🔴"),
        ],
        row=3
    )
    async def safety_select(self, interaction: discord.Interaction, select: ui.Select):
        """Altera o nível de segurança."""
        await self.db.set_channel_settings(
            self.channel_id,
            None,
            safety_mode=select.values[0]
        )
        await self.refresh()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)


class ConfigCommands(commands.Cog):
    """Comandos de configuração do bot."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config
        self.db: DatabaseManager = bot.db
        self.permission = PermissionChecker(self.config)
    
    # === Grupo Config ===
    
    config_group = app_commands.Group(
        name="config",
        description="Configurações do bot"
    )
    
    @config_group.command(name="painel", description="Abre o painel de configuração interativo")
    async def config_panel(self, interaction: discord.Interaction):
        """Abre o painel de configuração."""
        if not self.permission.check_permissions(interaction, admin_only=True):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        view = ConfigView(interaction.channel_id, self.db)
        await view.refresh()
        
        await interaction.response.send_message(
            embed=view.create_embed(),
            view=view,
            ephemeral=True
        )
    
    @config_group.command(name="ativar", description="Ativa o bot neste canal")
    async def config_enable(self, interaction: discord.Interaction):
        """Ativa o bot no canal."""
        if not self.permission.check_permissions(interaction, admin_only=True):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        await self.db.set_channel_active(interaction.channel_id, True)
        
        embed = discord.Embed(
            title="✅ Bot Ativado",
            description=f"O bot agora está ativo em {interaction.channel.mention}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @config_group.command(name="desativar", description="Desativa o bot neste canal")
    async def config_disable(self, interaction: discord.Interaction):
        """Desativa o bot no canal."""
        if not self.permission.check_permissions(interaction, admin_only=True):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        await self.db.set_channel_active(interaction.channel_id, False)
        
        embed = discord.Embed(
            title="🔴 Bot Desativado",
            description=f"O bot foi desativado em {interaction.channel.mention}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @config_group.command(name="modo", description="Define o modo de operação do bot")
    @app_commands.describe(
        modo="Modo de operação"
    )
    @app_commands.choices(modo=[
        app_commands.Choice(name="Desativado", value=0),
        app_commands.Choice(name="Inteligente", value=1),
        app_commands.Choice(name="Fluido", value=3),
        app_commands.Choice(name="Frenético", value=4),
        app_commands.Choice(name="Roleplay", value=5),
    ])
    async def config_mode(
        self,
        interaction: discord.Interaction,
        modo: app_commands.Choice[int]
    ):
        """Define o modo do chatbot."""
        if not self.permission.check_permissions(interaction, admin_only=True):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        await self.db.set_channel_settings(
            interaction.channel_id,
            interaction.guild_id,
            chatbot_mode=modo.value
        )
        
        descriptions = {
            0: "Bot desativado neste canal",
            1: "Bot responde apenas quando mencionado ou em reply",
            3: "Bot participa ativamente das conversas",
            4: "Bot responde a todas as mensagens",
            5: "Modo roleplay com persona ativa"
        }
        
        embed = discord.Embed(
            title="🎮 Modo Alterado",
            description=f"Modo: **{modo.name}**\n{descriptions.get(modo.value, '')}",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @config_group.command(name="gatilhos", description="Define quando o bot deve responder")
    @app_commands.describe(
        modo="Modo de gatilho"
    )
    @app_commands.choices(modo=[
        app_commands.Choice(name="Menção/Reply", value="standard"),
        app_commands.Choice(name="Prefixo (!)", value="prefix"),
        app_commands.Choice(name="Todos", value="all"),
        app_commands.Choice(name="Desativado", value="off"),
    ])
    async def config_triggers(
        self,
        interaction: discord.Interaction,
        modo: app_commands.Choice[str]
    ):
        """Define os gatilhos de resposta."""
        if not self.permission.check_permissions(interaction, admin_only=True):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        await self.db.set_channel_settings(
            interaction.channel_id,
            interaction.guild_id,
            trigger_mode=modo.value
        )
        
        descriptions = {
            "standard": "Bot responde quando mencionado ou em reply",
            "prefix": "Bot responde a mensagens começando com !",
            "all": "Bot responde a menções, replies e prefixo",
            "off": "Gatilhos manuais desativados (modo autônomo)"
        }
        
        embed = discord.Embed(
            title="🔔 Gatilhos Alterados",
            description=f"Modo: **{modo.name}**\n{descriptions.get(modo.value, '')}",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @config_group.command(name="memoria", description="Ativa ou desativa a memória do bot")
    @app_commands.describe(
        ativar="Ativar ou desativar memória"
    )
    async def config_memory(
        self,
        interaction: discord.Interaction,
        ativar: bool
    ):
        """Configura uso de memória."""
        if not self.permission.check_permissions(interaction, admin_only=True):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        await self.db.set_channel_settings(
            interaction.channel_id,
            interaction.guild_id,
            use_memory=ativar
        )
        
        status = "ativada" if ativar else "desativada"
        embed = discord.Embed(
            title="🧠 Memória",
            description=f"Memória **{status}** neste canal.",
            color=discord.Color.green() if ativar else discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @config_group.command(name="contexto", description="Define o modo de contexto")
    @app_commands.describe(
        modo="Modo de contexto"
    )
    @app_commands.choices(modo=[
        app_commands.Choice(name="Normal (Chat Completion)", value="normal"),
        app_commands.Choice(name="Assistant API", value="assistant"),
    ])
    async def config_context(
        self,
        interaction: discord.Interaction,
        modo: app_commands.Choice[str]
    ):
        """Define o modo de contexto."""
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
        
        if modo.value == "assistant":
            description = (
                "Modo Assistant API ativado.\n"
                "Use `/config assistente <id>` para definir o Assistant ID."
            )
        else:
            description = "Modo Normal ativado (Chat Completion)."
        
        embed = discord.Embed(
            title="🔄 Modo de Contexto",
            description=description,
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @config_group.command(name="assistente", description="Define o ID do Assistant (modo Assistant)")
    @app_commands.describe(
        assistant_id="ID do Assistant da OpenAI"
    )
    async def config_assistant(
        self,
        interaction: discord.Interaction,
        assistant_id: str
    ):
        """Define o Assistant ID."""
        if not self.permission.check_permissions(interaction, admin_only=True):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        await self.db.set_channel_settings(
            interaction.channel_id,
            interaction.guild_id,
            assistant_id=assistant_id
        )
        
        embed = discord.Embed(
            title="🤖 Assistant Configurado",
            description=f"Assistant ID: `{assistant_id}`",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Próximo passo",
            value="Use `/config contexto assistant` para ativar o modo Assistant",
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @config_group.command(name="info", description="Mostra configurações atuais do canal")
    async def config_info(self, interaction: discord.Interaction):
        """Mostra configurações atuais."""
        settings = await self.db.get_channel_settings(interaction.channel_id)
        
        if not settings:
            await interaction.response.send_message(
                "ℹ️ Nenhuma configuração encontrada para este canal.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="📋 Configurações Atuais",
            description=f"Canal: {interaction.channel.mention}",
            color=discord.Color.blue()
        )
        
        for key, value in settings.items():
            if value is not None and key not in ["id", "created_at", "updated_at"]:
                embed.add_field(
                    name=key.replace("_", " ").title(),
                    value=str(value)[:100],
                    inline=True
                )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(ConfigCommands(bot))
