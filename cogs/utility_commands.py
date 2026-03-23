"""
Comandos de Utilidade
Comandos diversos e úteis
"""

import logging
import random
from datetime import datetime
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from core.config import Config
from database.manager import DatabaseManager
from utils.permission_checker import PermissionChecker, permission_denied_message

logger = logging.getLogger("discord-bot")


class UtilityCommands(commands.Cog):
    """Comandos utilitários."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config
        self.db: DatabaseManager = bot.db
        self.permission = PermissionChecker(self.config)
    
    @app_commands.command(name="ajuda", description="Mostra a ajuda do bot")
    async def help_command(self, interaction: discord.Interaction):
        """Mostra ajuda do bot."""
        embed = discord.Embed(
            title="🤖 Bot de IA Avançada - Ajuda",
            description="Lista de comandos disponíveis",
            color=discord.Color.blue()
        )
        
        # Chat
        embed.add_field(
            name="💬 Chat",
            value=(
                "`/chat <mensagem>` - Conversa com o bot\n"
                "`/limpar` - Limpa histórico do canal\n"
                "`/historico` - Mostra suas estatísticas"
            ),
            inline=False
        )
        
        # Configuração
        embed.add_field(
            name="⚙️ Configuração",
            value=(
                "`/config painel` - Painel interativo\n"
                "`/config ativar/desativar` - Ativa/desativa bot\n"
                "`/config modo` - Modo de operação\n"
                "`/config gatilhos` - Como o bot responde\n"
                "`/config memoria` - Ativa/desativa memória"
            ),
            inline=False
        )
        
        # Modelos
        embed.add_field(
            name="🧠 Modelos",
            value=(
                "`/modelo listar` - Lista modelos\n"
                "`/modelo usar <nome>` - Seleciona modelo\n"
                "`/modelo adicionar` - Adiciona modelo customizado"
            ),
            inline=False
        )
        
        # Personas
        embed.add_field(
            name="🎭 Personas",
            value=(
                "`/persona listar` - Lista personas\n"
                "`/persona usar <nome>` - Ativa persona\n"
                "`/persona criar` - Cria nova persona\n"
                "`/persona exportar/importar` - Compartilha personas"
            ),
            inline=False
        )
        
        # Imagens
        embed.add_field(
            name="🎨 Imagens",
            value=(
                "`/imagem <prompt>` - Gera uma imagem\n"
                "`/cotas` - Verifica suas cotas"
            ),
            inline=False
        )
        
        # Loja
        embed.add_field(
            name="🛒 Loja",
            value=(
                "`/loja itens` - Lista itens\n"
                "`/loja comprar` - Compra item\n"
                "`/loja saldo` - Seu saldo\n"
                "`/loja daily` - Recompensa diária\n"
                "`/top` - Ranking"
            ),
            inline=False
        )
        
        # Arquivos
        embed.add_field(
            name="📁 Arquivos",
            value=(
                "`/arquivo enviar` - Envia arquivo\n"
                "`/arquivo listar` - Seus arquivos\n"
                "`/arquivo baixar` - Baixa arquivo"
            ),
            inline=False
        )
        
        # Utilidades
        embed.add_field(
            name="🔧 Utilidades",
            value=(
                "`/lembrar <tempo> <mensagem>` - Define lembrete\n"
                "`/lembretes` - Lista lembretes\n"
                "`/traduzir <texto>` - Traduz texto\n"
                "`/resumir` - Resume conversa"
            ),
            inline=False
        )
        
        embed.set_footer(text="Use /ajuda_completa para mais detalhes")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="ping", description="Verifica a latência do bot")
    async def ping_command(self, interaction: discord.Interaction):
        """Mostra latência do bot."""
        latency = round(self.bot.latency * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latência: **{latency}ms**",
            color=discord.Color.green() if latency < 200 else discord.Color.yellow() if latency < 500 else discord.Color.red()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="info", description="Informações sobre o bot")
    async def info_command(self, interaction: discord.Interaction):
        """Mostra informações do bot."""
        embed = discord.Embed(
            title="🤖 Bot de IA Avançada",
            description="Um bot de Discord completo com múltiplos modelos de IA",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📊 Estatísticas",
            value=(
                f"Servidores: {len(self.bot.guilds)}\n"
                f"Usuários: {sum(g.member_count for g in self.bot.guilds)}\n"
                f"Latência: {round(self.bot.latency * 1000)}ms"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🧠 Modelos",
            value=str(len(self.config.models)),
            inline=True
        )
        
        embed.add_field(
            name="⚙️ Versão",
            value="2.0.0",
            inline=True
        )
        
        embed.set_footer(text="Desenvolvido com ❤️")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="dado", description="Rola um dado")
    @app_commands.describe(
        lados="Número de lados do dado",
        quantidade="Quantidade de dados"
    )
    async def dice_command(
        self,
        interaction: discord.Interaction,
        lados: int = 6,
        quantidade: int = 1
    ):
        """Rola dados."""
        if lados < 2 or lados > 100:
            await interaction.response.send_message(
                "❌ O dado deve ter entre 2 e 100 lados.",
                ephemeral=True
            )
            return
        
        if quantidade < 1 or quantidade > 20:
            await interaction.response.send_message(
                "❌ Você pode rolar entre 1 e 20 dados.",
                ephemeral=True
            )
            return
        
        results = [random.randint(1, lados) for _ in range(quantidade)]
        total = sum(results)
        
        if quantidade == 1:
            result_text = f"🎲 **{results[0]}**"
        else:
            result_text = f"🎲 **{total}** ({', '.join(map(str, results))})"
        
        embed = discord.Embed(
            title=f"Rolando {quantidade}d{lados}",
            description=result_text,
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="moeda", description="Joga uma moeda")
    async def coin_command(self, interaction: discord.Interaction):
        """Joga uma moeda."""
        result = random.choice(["Cara", "Coroa"])
        emoji = "🪙" if result == "Cara" else "💿"
        
        embed = discord.Embed(
            title=f"{emoji} {result}!",
            color=discord.Color.gold()
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="sortear", description="Sorteia um membro do servidor")
    async def raffle_command(self, interaction: discord.Interaction):
        """Sorteia um membro."""
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ Este comando só funciona em servidores.",
                ephemeral=True
            )
            return
        
        members = [m for m in interaction.guild.members if not m.bot]
        
        if not members:
            await interaction.response.send_message(
                "❌ Não há membros para sortear.",
                ephemeral=True
            )
            return
        
        winner = random.choice(members)
        
        embed = discord.Embed(
            title="🎉 Sorteado!",
            description=f"**{winner.mention}** foi sorteado!",
            color=discord.Color.gold()
        )
        
        if winner.avatar:
            embed.set_thumbnail(url=winner.avatar.url)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="avatar", description="Mostra o avatar de um usuário")
    @app_commands.describe(usuario="Usuário (deixe em branco para ver o seu)")
    async def avatar_command(
        self,
        interaction: discord.Interaction,
        usuario: Optional[discord.Member] = None
    ):
        """Mostra avatar."""
        target = usuario or interaction.user
        
        if not target.avatar:
            await interaction.response.send_message(
                "❌ Este usuário não tem avatar.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f"🖼️ Avatar de {target.display_name}",
            color=discord.Color.blue()
        )
        embed.set_image(url=target.avatar.url)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="serverinfo", description="Informações sobre o servidor")
    async def serverinfo_command(self, interaction: discord.Interaction):
        """Mostra informações do servidor."""
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ Este comando só funciona em servidores.",
                ephemeral=True
            )
            return
        
        guild = interaction.guild
        
        embed = discord.Embed(
            title=f"📊 {guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Dono", value=guild.owner.mention if guild.owner else "Desconhecido", inline=True)
        embed.add_field(name="Criado em", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
        
        embed.add_field(name="Membros", value=guild.member_count, inline=True)
        embed.add_field(name="Canais", value=len(guild.channels), inline=True)
        embed.add_field(name="Cargos", value=len(guild.roles), inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="userinfo", description="Informações sobre um usuário")
    @app_commands.describe(usuario="Usuário (deixe em branco para ver o seu)")
    async def userinfo_command(
        self,
        interaction: discord.Interaction,
        usuario: Optional[discord.Member] = None
    ):
        """Mostra informações do usuário."""
        target = usuario or interaction.user
        
        embed = discord.Embed(
            title=f"👤 {target.display_name}",
            color=target.color if target.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        if target.avatar:
            embed.set_thumbnail(url=target.avatar.url)
        
        embed.add_field(name="ID", value=target.id, inline=True)
        embed.add_field(name="Nome", value=target.name, inline=True)
        embed.add_field(name="Apelido", value=target.nick or "Nenhum", inline=True)
        
        embed.add_field(
            name="Entrou no servidor",
            value=target.joined_at.strftime("%d/%m/%Y") if target.joined_at else "Desconhecido",
            inline=True
        )
        embed.add_field(
            name="Conta criada",
            value=target.created_at.strftime("%d/%m/%Y"),
            inline=True
        )
        
        roles = [r.mention for r in target.roles if r.name != "@everyone"]
        if roles:
            embed.add_field(
                name=f"Cargos ({len(roles)})",
                value=" ".join(roles[:10]) + ("..." if len(roles) > 10 else ""),
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(UtilityCommands(bot))
