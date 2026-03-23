"""
Instância principal do Bot Discord
Gerencia o cliente, eventos e sincronização de comandos
"""

import asyncio
import logging
import traceback
from datetime import datetime
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands, tasks

from core.config import Config
from database.manager import DatabaseManager
from providers.manager import ProviderManager
from utils.status_manager import StatusManager
from utils.permission_checker import PermissionChecker

logger = logging.getLogger("discord-bot")


class BotInstance:
    """Classe principal que gerencia a instância do bot."""
    
    def __init__(self, config: Config, db: DatabaseManager):
        self.config = config
        self.db = db
        self.provider = ProviderManager(config)
        self.client: Optional[commands.Bot] = None
        self.tree: Optional[app_commands.CommandTree] = None
        self.status_manager: Optional[StatusManager] = None
        self.permission_checker: Optional[PermissionChecker] = None
        self._shutdown_event = asyncio.Event()
        
    async def start(self):
        """Inicializa e inicia o bot."""
        # Configurar intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.reactions = True
        intents.presences = True
        
        # Criar atividade inicial
        activity = self._create_activity()
        
        # Criar cliente do bot
        self.client = commands.Bot(
            command_prefix=self.config.trigger_config.prefix,
            intents=intents,
            activity=activity,
            status=discord.Status.online,
            help_command=None  # Desabilitar comando help padrão
        )
        
        self.tree = self.client.tree
        self.status_manager = StatusManager(self.client, self.config)
        self.permission_checker = PermissionChecker(self.config)
        
        # Adicionar atributos ao bot para acesso pelos cogs
        self.client.config = self.config
        self.client.db = self.db
        self.client.provider = self.provider
        
        # Registrar eventos
        self._register_events()
        
        # Carregar cogs
        await self._load_cogs()
        
        # Iniciar tarefas em background
        self.backup_task.start()
        self.status_rotation_task.start()
        
        # Iniciar o bot
        try:
            await self.client.start(self.config.bot_token)
        except Exception as e:
            logger.error(f"Erro ao iniciar bot: {e}")
            raise
    
    def _create_activity(self) -> discord.Activity:
        """Cria a atividade inicial do bot."""
        status_msg = self.config.status_message
        status_type = self.config.status_type.lower()
        
        activity_type = discord.ActivityType.watching
        if status_type == "playing":
            activity_type = discord.ActivityType.playing
        elif status_type == "listening":
            activity_type = discord.ActivityType.listening
        elif status_type == "competing":
            activity_type = discord.ActivityType.competing
        
        return discord.Activity(type=activity_type, name=status_msg)
    
    def _register_events(self):
        """Registra todos os eventos do bot."""
        
        @self.client.event
        async def on_ready():
            """Evento disparado quando o bot está pronto."""
            logger.info(f"✅ Bot conectado como {self.client.user}")
            logger.info(f"📊 Servidores: {len(self.client.guilds)}")
            logger.info(f"👥 Usuários: {sum(g.member_count for g in self.client.guilds)}")
            
            # Sincronizar comandos
            try:
                synced = await self.tree.sync()
                logger.info(f"🔄 Comandos sincronizados: {len(synced)}")
            except Exception as e:
                logger.error(f"❌ Erro ao sincronizar comandos: {e}")
            
            # Inicializar status rotativo
            await self.status_manager.start_rotation()
        
        @self.client.event
        async def on_guild_join(guild: discord.Guild):
            """Evento quando o bot entra em um novo servidor."""
            logger.info(f"➕ Entrou no servidor: {guild.name} (ID: {guild.id})")
            
            # Criar configurações padrão para o servidor
            await self.db.create_guild_config(guild.id)
            
            # Enviar mensagem de boas-vindas
            await self._send_welcome_message(guild)
        
        @self.client.event
        async def on_guild_remove(guild: discord.Guild):
            """Evento quando o bot sai de um servidor."""
            logger.info(f"➖ Saiu do servidor: {guild.name} (ID: {guild.id})")
        
        @self.client.event
        async def on_command_error(ctx: commands.Context, error):
            """Handler de erros de comandos."""
            if isinstance(error, commands.CommandNotFound):
                return
            
            logger.error(f"Erro no comando: {error}")
            
            embed = discord.Embed(
                title="❌ Erro",
                description=str(error),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
        
        @self.client.event
        async def on_app_command_error(interaction: discord.Interaction, error):
            """Handler de erros de comandos de app."""
            logger.error(f"Erro no comando app: {error}")
            
            if interaction.response.is_done():
                await interaction.followup.send(
                    f"❌ Ocorreu um erro: {str(error)}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"❌ Ocorreu um erro: {str(error)}",
                    ephemeral=True
                )
    
    async def _send_welcome_message(self, guild: discord.Guild):
        """Envia mensagem de boas-vindas em um canal do servidor."""
        # Procurar canal adequado
        channel = None
        
        # Tentar canal de sistema
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            channel = guild.system_channel
        
        # Tentar canal geral
        if not channel:
            for ch in guild.text_channels:
                if ch.name in ["geral", "general", "chat", "principal"]:
                    if ch.permissions_for(guild.me).send_messages:
                        channel = ch
                        break
        
        # Primeiro canal disponível
        if not channel:
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).send_messages:
                    channel = ch
                    break
        
        if channel:
            embed = discord.Embed(
                title="🤖 Olá! Eu sou o Bot de IA Avançada!",
                description=(
                    "Obrigado por me adicionar ao seu servidor!\n\n"
                    "**🚀 Comece aqui:**\n"
                    "• Use `/config painel` para configurar o bot\n"
                    "• Use `/modelo listar` para ver modelos disponíveis\n"
                    "• Use `/ajuda` para ver todos os comandos\n\n"
                    "**✨ Funcionalidades principais:**\n"
                    "• Chat inteligente com múltiplos modelos\n"
                    "• Modo Assistant com ferramentas\n"
                    "• Geração de imagens\n"
                    "• Sistema de memória e RAG\n"
                    "• Personas customizáveis"
                ),
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.set_footer(text="Bot de IA Avançada v2.0")
            
            try:
                await channel.send(embed=embed)
            except Exception as e:
                logger.warning(f"Não foi possível enviar mensagem de boas-vindas: {e}")
    
    async def _load_cogs(self):
        """Carrega todos os cogs/módulos do bot."""
        cogs = [
            "cogs.chat_commands",
            "cogs.config_commands",
            "cogs.model_commands",
            "cogs.persona_commands",
            "cogs.image_commands",
            "cogs.shop_commands",
            "cogs.memory_commands",
            "cogs.file_commands",
            "cogs.utility_commands",
            "cogs.apps_commands",
            "cogs.admin_commands",
        ]
        
        for cog in cogs:
            try:
                await self.client.load_extension(cog)
                logger.info(f"📦 Cog carregado: {cog}")
            except Exception as e:
                logger.error(f"❌ Erro ao carregar cog {cog}: {e}")
                logger.error(traceback.format_exc())
    
    @tasks.loop(minutes=120)
    async def backup_task(self):
        """Tarefa de backup automático do banco de dados."""
        try:
            backup_path = await self.db.create_backup()
            logger.info(f"💾 Backup criado: {backup_path}")
        except Exception as e:
            logger.error(f"❌ Erro ao criar backup: {e}")
    
    @backup_task.before_loop
    async def before_backup(self):
        """Espera o bot estar pronto antes de iniciar backups."""
        await self.client.wait_until_ready()
    
    @tasks.loop(minutes=5)
    async def status_rotation_task(self):
        """Rotação automática de status."""
        if self.status_manager:
            await self.status_manager.rotate_status()
    
    @status_rotation_task.before_loop
    async def before_status_rotation(self):
        """Espera o bot estar pronto antes de rotacionar status."""
        await self.client.wait_until_ready()
    
    async def cleanup(self):
        """Limpa recursos ao encerrar."""
        logger.info("🧹 Limpando recursos...")
        
        if self.backup_task.is_running():
            self.backup_task.cancel()
        
        if self.status_rotation_task.is_running():
            self.status_rotation_task.cancel()
        
        if self.client:
            await self.client.close()
        
        if self.db:
            await self.db.close()
        
        logger.info("✅ Cleanup concluído")
    
    async def shutdown(self):
        """Sinaliza para o bot desligar."""
        self._shutdown_event.set()
