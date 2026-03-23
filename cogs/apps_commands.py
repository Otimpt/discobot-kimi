"""
Comandos de Apps
Apps diversos como tradução, resumo, etc.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from core.config import Config
from database.manager import DatabaseManager
from providers.manager import ProviderManager
from utils.permission_checker import PermissionChecker, permission_denied_message

logger = logging.getLogger("discord-bot")


class AppsCommands(commands.Cog):
    """Apps diversos do bot."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config
        self.db: DatabaseManager = bot.db
        self.provider: ProviderManager = bot.provider
        self.permission = PermissionChecker(self.config)
    
    @app_commands.command(name="traduzir", description="Traduz texto para outro idioma")
    @app_commands.describe(
        texto="Texto a traduzir",
        idioma="Idioma de destino"
    )
    @app_commands.choices(idioma=[
        app_commands.Choice(name="Português", value="português"),
        app_commands.Choice(name="Inglês", value="inglês"),
        app_commands.Choice(name="Espanhol", value="espanhol"),
        app_commands.Choice(name="Francês", value="francês"),
        app_commands.Choice(name="Alemão", value="alemão"),
        app_commands.Choice(name="Italiano", value="italiano"),
        app_commands.Choice(name="Japonês", value="japonês"),
        app_commands.Choice(name="Coreano", value="coreano"),
        app_commands.Choice(name="Chinês", value="chinês"),
        app_commands.Choice(name="Russo", value="russo"),
    ])
    async def translate_command(
        self,
        interaction: discord.Interaction,
        texto: str,
        idioma: app_commands.Choice[str]
    ):
        """Traduz texto."""
        if not self.permission.check_permissions(interaction):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            prompt = f"Traduza o seguinte texto para {idioma.value}:\n\n{texto}\n\nTradução:"
            
            response = await self.provider.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o-mini"
            )
            
            embed = discord.Embed(
                title=f"🌐 Tradução para {idioma.name}",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Original",
                value=texto[:500] + "..." if len(texto) > 500 else texto,
                inline=False
            )
            embed.add_field(
                name="Tradução",
                value=response["content"][:1000],
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro na tradução: {e}")
            await interaction.followup.send(
                f"❌ Erro ao traduzir: {e}",
                ephemeral=True
            )
    
    @app_commands.command(name="resumir", description="Resume uma conversa ou texto")
    @app_commands.describe(
        mensagens="Número de mensagens para resumir (padrão: 50)",
        estilo="Estilo do resumo"
    )
    @app_commands.choices(estilo=[
        app_commands.Choice(name="Conciso", value="conciso"),
        app_commands.Choice(name="Detalhado", value="detalhado"),
        app_commands.Choice(name="Pontos principais", value="pontos"),
        app_commands.Choice(name="Tópicos", value="topicos"),
    ])
    async def summarize_command(
        self,
        interaction: discord.Interaction,
        mensagens: Optional[int] = 50,
        estilo: Optional[app_commands.Choice[str]] = None
    ):
        """Resume conversa."""
        if not self.permission.check_permissions(interaction):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Buscar mensagens
            history = await self.db.get_conversation_history(
                interaction.channel_id,
                limit=min(mensagens, 100)
            )
            
            if not history:
                await interaction.followup.send(
                    "📭 Não há mensagens para resumir.",
                    ephemeral=True
                )
                return
            
            # Construir texto
            conversation = []
            for msg in history:
                user = self.bot.get_user(msg["user_id"])
                user_name = user.display_name if user else f"User_{msg['user_id']}"
                conversation.append(f"{user_name}: {msg['content']}")
            
            conversation_text = "\n".join(conversation)
            
            style = estilo.value if estilo else "conciso"
            
            prompts = {
                "conciso": "Faça um resumo conciso (máximo 3 parágrafos):",
                "detalhado": "Faça um resumo detalhado cobrindo todos os pontos importantes:",
                "pontos": "Liste os pontos principais da conversa:",
                "topicos": "Organize o resumo por tópicos:"
            }
            
            prompt = f"{prompts.get(style, prompts['conciso'])}\n\n{conversation_text}\n\nResumo:"
            
            response = await self.provider.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o-mini"
            )
            
            embed = discord.Embed(
                title=f"📝 Resumo ({len(history)} mensagens)",
                description=response["content"][:4000],
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.set_footer(text=f"Estilo: {style}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro no resumo: {e}")
            await interaction.followup.send(
                f"❌ Erro ao resumir: {e}",
                ephemeral=True
            )
    
    @app_commands.command(name="analisar", description="Analisa o sentimento de um texto")
    @app_commands.describe(texto="Texto para analisar")
    async def analyze_command(
        self,
        interaction: discord.Interaction,
        texto: str
    ):
        """Analisa sentimento."""
        if not self.permission.check_permissions(interaction):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            prompt = f"""Analise o sentimento do seguinte texto. 
            Responda em JSON com: sentimento (positivo/negativo/neutro), 
            intensidade (1-10), e palavras_chave (lista).
            
            Texto: {texto}"""
            
            response = await self.provider.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o-mini"
            )
            
            embed = discord.Embed(
                title="📊 Análise de Sentimento",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Texto",
                value=texto[:200] + "..." if len(texto) > 200 else texto,
                inline=False
            )
            embed.add_field(
                name="Análise",
                value=response["content"][:1000],
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro na análise: {e}")
            await interaction.followup.send(
                f"❌ Erro ao analisar: {e}",
                ephemeral=True
            )
    
    @app_commands.command(name="perguntar", description="Faz uma pergunta sobre um texto")
    @app_commands.describe(
        texto="Texto base",
        pergunta="Sua pergunta sobre o texto"
    )
    async def ask_command(
        self,
        interaction: discord.Interaction,
        texto: str,
        pergunta: str
    ):
        """Pergunta sobre texto."""
        if not self.permission.check_permissions(interaction):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            prompt = f"""Texto: {texto}
            
            Pergunta: {pergunta}
            
            Responda baseado apenas no texto fornecido."""
            
            response = await self.provider.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o-mini"
            )
            
            embed = discord.Embed(
                title="❓ Pergunta & Resposta",
                color=discord.Color.blue()
            )
            embed.add_field(name="Pergunta", value=pergunta, inline=False)
            embed.add_field(name="Resposta", value=response["content"][:1000], inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro na pergunta: {e}")
            await interaction.followup.send(
                f"❌ Erro ao processar: {e}",
                ephemeral=True
            )
    
    @app_commands.command(name="corrigir", description="Corrige gramática e ortografia")
    @app_commands.describe(texto="Texto para corrigir")
    async def correct_command(
        self,
        interaction: discord.Interaction,
        texto: str
    ):
        """Corrige texto."""
        if not self.permission.check_permissions(interaction):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            prompt = f"""Corrija a gramática e ortografia do seguinte texto. 
            Mantenha o significado original e o tom.
            
            Texto: {texto}
            
            Texto corrigido:"""
            
            response = await self.provider.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o-mini"
            )
            
            embed = discord.Embed(
                title="✏️ Correção",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Original",
                value=texto[:500] + "..." if len(texto) > 500 else texto,
                inline=False
            )
            embed.add_field(
                name="Corrigido",
                value=response["content"][:1000],
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro na correção: {e}")
            await interaction.followup.send(
                f"❌ Erro ao corrigir: {e}",
                ephemeral=True
            )
    
    @app_commands.command(name="explicar", description="Explica um conceito de forma simples")
    @app_commands.describe(
        conceito="Conceito a explicar",
        nivel="Nível de detalhe"
    )
    @app_commands.choices(nivel=[
        app_commands.Choice(name="Criança (5 anos)", value="crianca"),
        app_commands.Choice(name="Iniciante", value="iniciante"),
        app_commands.Choice(name="Intermediário", value="intermediario"),
        app_commands.Choice(name="Avançado", value="avancado"),
    ])
    async def explain_command(
        self,
        interaction: discord.Interaction,
        conceito: str,
        nivel: Optional[app_commands.Choice[str]] = None
    ):
        """Explica conceito."""
        if not self.permission.check_permissions(interaction):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            level = nivel.value if nivel else "iniciante"
            
            levels = {
                "crianca": "Explique como se estivesse falando com uma criança de 5 anos",
                "iniciante": "Explique para alguém sem conhecimento prévio",
                "intermediario": "Explique com detalhes técnicos moderados",
                "avancado": "Explique com terminologia técnica avançada"
            }
            
            prompt = f"{levels.get(level, levels['iniciante'])}:\n\n{conceito}"
            
            response = await self.provider.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o-mini"
            )
            
            embed = discord.Embed(
                title=f"📚 {conceito}",
                description=response["content"][:4000],
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Nível: {nivel.name if nivel else 'Iniciante'}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro na explicação: {e}")
            await interaction.followup.send(
                f"❌ Erro ao explicar: {e}",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(AppsCommands(bot))
