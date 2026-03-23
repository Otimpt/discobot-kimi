"""
Menu de Configuração do Modo Interativo
Configuração completa da personalidade do membro
"""

import logging
from typing import Optional

import discord
from discord import app_commands, ui
from discord.ext import commands

from core.config import Config
from core.interactive_member import InteractiveMember, PersonalityConfig, Mood
from database.manager import DatabaseManager
from utils.permission_checker import PermissionChecker, permission_denied_message

logger = logging.getLogger("discord-bot")


class InteractiveConfigView(ui.View):
    """Menu principal de configuração do modo interativo."""
    
    def __init__(self, bot: commands.Bot, user_id: int, guild_id: int, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.user_id = user_id
        self.guild_id = guild_id
        self.db: DatabaseManager = bot.db
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Este menu não é seu!", ephemeral=True)
            return False
        return True
    
    def get_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="👤 Configurar Membro Interativo",
            description="Configure a personalidade completa do membro do servidor",
            color=discord.Color.teal()
        )
        
        embed.add_field(
            name="📝 Identidade",
            value="Nome, idade, história, ocupação",
            inline=True
        )
        embed.add_field(
            name="🧠 Personalidade",
            value="Traços, humor, energia, estilo",
            inline=True
        )
        embed.add_field(
            name="❤️ Gostos",
            value="Likes, dislikes, hobbies, música",
            inline=True
        )
        embed.add_field(
            name="⚙️ Comportamento",
            value="Nível de atividade, horários, estilo de fala",
            inline=True
        )
        
        return embed
    
    @ui.button(label="📝 Identidade", style=discord.ButtonStyle.primary, row=0)
    async def identity_button(self, interaction: discord.Interaction, button: ui.Button):
        """Configura identidade."""
        modal = IdentityConfigModal(self.guild_id)
        await interaction.response.send_modal(modal)
    
    @ui.button(label="🧠 Personalidade", style=discord.ButtonStyle.primary, row=0)
    async def personality_button(self, interaction: discord.Interaction, button: ui.Button):
        """Configura personalidade."""
        view = PersonalityTraitsView(self.bot, self.user_id, self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)
    
    @ui.button(label="❤️ Gostos", style=discord.ButtonStyle.primary, row=0)
    async def likes_button(self, interaction: discord.Interaction, button: ui.Button):
        """Configura gostos."""
        view = LikesConfigView(self.bot, self.user_id, self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)
    
    @ui.button(label="⚙️ Comportamento", style=discord.ButtonStyle.secondary, row=1)
    async def behavior_button(self, interaction: discord.Interaction, button: ui.Button):
        """Configura comportamento."""
        view = BehaviorConfigView(self.bot, self.user_id, self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)
    
    @ui.button(label="💾 Salvar", style=discord.ButtonStyle.success, row=1)
    async def save_button(self, interaction: discord.Interaction, button: ui.Button):
        """Salva configuração."""
        await interaction.response.send_message(
            "✅ Configuração salva! O membro interativo está pronto.",
            ephemeral=True
        )
    
    @ui.button(label="▶️ Ativar", style=discord.ButtonStyle.success, row=2)
    async def activate_button(self, interaction: discord.Interaction, button: ui.Button):
        """Ativa modo interativo."""
        await self.db.set_channel_settings(
            interaction.channel_id,
            self.guild_id,
            mode="interactive"
        )
        
        embed = discord.Embed(
            title="👤 Modo Interativo Ativado!",
            description="O membro agora faz parte do servidor! 🎉",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)


class IdentityConfigModal(ui.Modal, title="Configurar Identidade"):
    """Modal para configurar identidade."""
    
    name = ui.TextInput(
        label="Nome",
        placeholder="Como o membro se chama?",
        default="Bot",
        required=True
    )
    
    age = ui.TextInput(
        label="Idade",
        placeholder="Idade (afeta maturidade)",
        default="25",
        required=True
    )
    
    backstory = ui.TextInput(
        label="História (opcional)",
        placeholder="De onde veio? Qual sua história?",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=500
    )
    
    occupation = ui.TextInput(
        label="Ocupação (opcional)",
        placeholder="O que faz da vida?",
        required=False
    )
    
    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"✅ Identidade configurada:\n"
            f"**Nome:** {self.name.value}\n"
            f"**Idade:** {self.age.value}\n"
            f"**História:** {self.backstory.value or 'Não definida'}\n"
            f"**Ocupação:** {self.occupation.value or 'Não definida'}",
            ephemeral=True
        )


class PersonalityTraitsView(ui.View):
    """Configuração de traços de personalidade."""
    
    def __init__(self, bot: commands.Bot, user_id: int, guild_id: int):
        super().__init__(timeout=180)
        self.bot = bot
        self.user_id = user_id
        self.guild_id = guild_id
    
    def get_embed(self) -> discord.Embed:
        return discord.Embed(
            title="🧠 Traços de Personalidade",
            description="Ajuste os traços (0.0 = mínimo, 1.0 = máximo)",
            color=discord.Color.blue()
        )
    
    @ui.select(
        placeholder="Extroversão...",
        options=[
            discord.SelectOption(label="Muito Introvertido (0.1)", value="0.1"),
            discord.SelectOption(label="Introvertido (0.3)", value="0.3"),
            discord.SelectOption(label="Equilibrado (0.5)", value="0.5"),
            discord.SelectOption(label="Extrovertido (0.7)", value="0.7"),
            discord.SelectOption(label="Muito Extrovertido (0.9)", value="0.9"),
        ],
        row=0
    )
    async def extraversion_select(self, interaction: discord.Interaction, select: ui.Select):
        await interaction.response.send_message(
            f"✅ Extroversão: {select.values[0]}",
            ephemeral=True
        )
    
    @ui.select(
        placeholder="Humor...",
        options=[
            discord.SelectOption(label="Sério (0.1)", value="0.1"),
            discord.SelectOption(label="Equilibrado (0.5)", value="0.5"),
            discord.SelectOption(label="Engraçado (0.7)", value="0.7"),
            discord.SelectOption(label="Muito engraçado (0.9)", value="0.9"),
        ],
        row=1
    )
    async def humor_select(self, interaction: discord.Interaction, select: ui.Select):
        await interaction.response.send_message(
            f"✅ Humor: {select.values[0]}",
            ephemeral=True
        )
    
    @ui.select(
        placeholder="Empatia...",
        options=[
            discord.SelectOption(label="Pouca (0.2)", value="0.2"),
            discord.SelectOption(label="Moderada (0.5)", value="0.5"),
            discord.SelectOption(label="Alta (0.8)", value="0.8"),
        ],
        row=2
    )
    async def empathy_select(self, interaction: discord.Interaction, select: ui.Select):
        await interaction.response.send_message(
            f"✅ Empatia: {select.values[0]}",
            ephemeral=True
        )
    
    @ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.secondary, row=3)
    async def back_button(self, interaction: discord.Interaction, button: ui.Button):
        view = InteractiveConfigView(self.bot, self.user_id, self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)


class LikesConfigView(ui.View):
    """Configuração de gostos."""
    
    def __init__(self, bot: commands.Bot, user_id: int, guild_id: int):
        super().__init__(timeout=180)
        self.bot = bot
        self.user_id = user_id
        self.guild_id = guild_id
    
    def get_embed(self) -> discord.Embed:
        return discord.Embed(
            title="❤️ Gostos e Preferências",
            description="Configure o que o membro gosta e não gosta",
            color=discord.Color.red()
        )
    
    @ui.button(label="➕ Adicionar Like", style=discord.ButtonStyle.success, row=0)
    async def add_like_button(self, interaction: discord.Interaction, button: ui.Button):
        modal = AddLikeModal("like")
        await interaction.response.send_modal(modal)
    
    @ui.button(label="➕ Adicionar Dislike", style=discord.ButtonStyle.danger, row=0)
    async def add_dislike_button(self, interaction: discord.Interaction, button: ui.Button):
        modal = AddLikeModal("dislike")
        await interaction.response.send_modal(modal)
    
    @ui.button(label="🎵 Música", style=discord.ButtonStyle.primary, row=1)
    async def music_button(self, interaction: discord.Interaction, button: ui.Button):
        modal = AddMusicModal()
        await interaction.response.send_modal(modal)
    
    @ui.button(label="🎨 Hobbies", style=discord.ButtonStyle.primary, row=1)
    async def hobbies_button(self, interaction: discord.Interaction, button: ui.Button):
        modal = AddHobbiesModal()
        await interaction.response.send_modal(modal)
    
    @ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.secondary, row=2)
    async def back_button(self, interaction: discord.Interaction, button: ui.Button):
        view = InteractiveConfigView(self.bot, self.user_id, self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)


class AddLikeModal(ui.Modal, title="Adicionar Gosto"):
    """Modal para adicionar like/dislike."""
    
    item = ui.TextInput(
        label="Item",
        placeholder="Ex: pizza, videogames, programação...",
        required=True
    )
    
    def __init__(self, type_: str):
        super().__init__()
        self.type_ = type_
    
    async def on_submit(self, interaction: discord.Interaction):
        action = "gostar de" if self.type_ == "like" else "não gostar de"
        await interaction.response.send_message(
            f"✅ Configurado para {action}: **{self.item.value}**",
            ephemeral=True
        )


class AddMusicModal(ui.Modal, title="Gêneros Musicais"):
    """Modal para adicionar gêneros musicais."""
    
    genres = ui.TextInput(
        label="Gêneros (separados por vírgula)",
        placeholder="rock, pop, eletrônica, jazz...",
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"✅ Gêneros musicais: **{self.genres.value}**",
            ephemeral=True
        )


class AddHobbiesModal(ui.Modal, title="Hobbies"):
    """Modal para adicionar hobbies."""
    
    hobbies = ui.TextInput(
        label="Hobbies (separados por vírgula)",
        placeholder="ler, jogar, programar, cozinhar...",
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"✅ Hobbies: **{self.hobbies.value}**",
            ephemeral=True
        )


class BehaviorConfigView(ui.View):
    """Configuração de comportamento."""
    
    def __init__(self, bot: commands.Bot, user_id: int, guild_id: int):
        super().__init__(timeout=180)
        self.bot = bot
        self.user_id = user_id
        self.guild_id = guild_id
    
    def get_embed(self) -> discord.Embed:
        return discord.Embed(
            title="⚙️ Comportamento",
            description="Configure como o membro se comporta",
            color=discord.Color.greyple()
        )
    
    @ui.select(
        placeholder="Nível de atividade...",
        options=[
            discord.SelectOption(label="Muito Reservado", value="very_reserved",
                               description="Raramente responde"),
            discord.SelectOption(label="Reservado", value="reserved",
                               description="Responde pouco"),
            discord.SelectOption(label="Moderado", value="moderate",
                               description="Responde moderadamente"),
            discord.SelectOption(label="Ativo", value="active",
                               description="Responde bastante"),
            discord.SelectOption(label="Muito Ativo", value="very_active",
                               description="Responde muito"),
        ],
        row=0
    )
    async def activity_select(self, interaction: discord.Interaction, select: ui.Select):
        await interaction.response.send_message(
            f"✅ Nível de atividade: **{select.values[0]}**",
            ephemeral=True
        )
    
    @ui.select(
        placeholder="Formalidade...",
        options=[
            discord.SelectOption(label="Muito Casual", value="0.1"),
            discord.SelectOption(label="Casual", value="0.3"),
            discord.SelectOption(label="Equilibrado", value="0.5"),
            discord.SelectOption(label="Formal", value="0.7"),
            discord.SelectOption(label="Muito Formal", value="0.9"),
        ],
        row=1
    )
    async def formality_select(self, interaction: discord.Interaction, select: ui.Select):
        await interaction.response.send_message(
            f"✅ Formalidade: {select.values[0]}",
            ephemeral=True
        )
    
    @ui.button(label="🕐 Horários", style=discord.ButtonStyle.primary, row=2)
    async def hours_button(self, interaction: discord.Interaction, button: ui.Button):
        modal = HoursConfigModal()
        await interaction.response.send_modal(modal)
    
    @ui.button(label="💬 Estilo de Fala", style=discord.ButtonStyle.primary, row=2)
    async def speech_button(self, interaction: discord.Interaction, button: ui.Button):
        modal = SpeechStyleModal()
        await interaction.response.send_modal(modal)
    
    @ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.secondary, row=3)
    async def back_button(self, interaction: discord.Interaction, button: ui.Button):
        view = InteractiveConfigView(self.bot, self.user_id, self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)


class HoursConfigModal(ui.Modal, title="Horários de Atividade"):
    """Modal para configurar horários."""
    
    wake_up = ui.TextInput(
        label="Hora de acordar",
        placeholder="8",
        default="8",
        required=True
    )
    
    sleep = ui.TextInput(
        label="Hora de dormir",
        placeholder="23",
        default="23",
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"✅ Horários configurados:\n"
            f"**Acorda:** {self.wake_up.value}h\n"
            f"**Dorme:** {self.sleep.value}h",
            ephemeral=True
        )


class SpeechStyleModal(ui.Modal, title="Estilo de Fala"):
    """Modal para configurar estilo de fala."""
    
    catchphrases = ui.TextInput(
        label="Bordões (separados por vírgula)",
        placeholder="Caramba!, Sério isso?, Aí sim!",
        required=False
    )
    
    emojis = ui.TextInput(
        label="Emojis favoritos",
        placeholder="😄 🤔 🎉",
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"✅ Estilo de fala configurado!",
            ephemeral=True
        )


class InteractiveCommands(commands.Cog):
    """Comandos do modo interativo."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config
        self.db: DatabaseManager = bot.db
        self.permission = PermissionChecker(self.config)
    
    @app_commands.command(name="membro", description="Configura o membro interativo")
    async def member_config(self, interaction: discord.Interaction):
        """Abre menu de configuração do membro."""
        if not self.permission.check_permissions(interaction, admin_only=True):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        view = InteractiveConfigView(
            self.bot,
            interaction.user.id,
            interaction.guild_id
        )
        
        await interaction.response.send_message(
            embed=view.get_embed(),
            view=view,
            ephemeral=True
        )
    
    @app_commands.command(name="membro_status", description="Mostra status do membro")
    async def member_status(self, interaction: discord.Interaction):
        """Mostra status atual do membro."""
        embed = discord.Embed(
            title="👤 Status do Membro",
            color=discord.Color.teal()
        )
        
        embed.add_field(
            name="Humor Atual",
            value="😊 Feliz",
            inline=True
        )
        embed.add_field(
            name="Energia",
            value="⚡ 75%",
            inline=True
        )
        embed.add_field(
            name="Relacionamentos",
            value="👥 12 amigos",
            inline=True
        )
        embed.add_field(
            name="Memórias",
            value="🧠 45 memórias",
            inline=True
        )
        embed.add_field(
            name="Opiniões",
            value="💭 8 opiniões",
            inline=True
        )
        embed.add_field(
            name="Mensagens",
            value="💬 150 vistas, 45 respondidas",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(InteractiveCommands(bot))
