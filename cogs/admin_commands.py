"""
Comandos de Administração
Comandos exclusivos para administradores
"""

import logging
from datetime import datetime
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from core.config import Config
from database.manager import DatabaseManager
from utils.permission_checker import PermissionChecker, permission_denied_message

logger = logging.getLogger("discord-bot")


class AdminCommands(commands.Cog):
    """Comandos administrativos."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config
        self.db: DatabaseManager = bot.db
        self.permission = PermissionChecker(self.config)
    
    admin_group = app_commands.Group(
        name="admin",
        description="Comandos administrativos",
        default_permissions=discord.Permissions(administrator=True)
    )
    
    @admin_group.command(name="tokens", description="Adiciona tokens a um usuário")
    @app_commands.describe(
        usuario="Usuário",
        quantidade="Quantidade de tokens",
        motivo="Motivo (opcional)"
    )
    async def admin_tokens(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        quantidade: int,
        motivo: Optional[str] = None
    ):
        """Adiciona tokens a um usuário."""
        if not self.permission.is_admin(interaction.user, interaction.guild):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        await self.db.add_tokens(usuario.id, quantidade)
        
        economy = await self.db.get_economy(usuario.id)
        
        embed = discord.Embed(
            title="💰 Tokens Adicionados",
            description=f"**{quantidade}** tokens adicionados para {usuario.mention}",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Novo Saldo",
            value=f"{economy['tokens']} tokens",
            inline=True
        )
        
        if motivo:
            embed.add_field(name="Motivo", value=motivo, inline=True)
        
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.avatar.url if interaction.user.avatar else None
        )
        
        await interaction.response.send_message(embed=embed)
        
        # Notificar usuário
        try:
            await usuario.send(
                f"💰 **{quantidade}** tokens foram adicionados à sua conta!\n"
                f"Novo saldo: **{economy['tokens']}** tokens\n"
                f"Motivo: {motivo or 'Não especificado'}"
            )
        except:
            pass
    
    @admin_group.command(name="cotas", description="Adiciona cotas de imagem a um usuário")
    @app_commands.describe(
        usuario="Usuário",
        quantidade="Quantidade de cotas"
    )
    async def admin_quota(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        quantidade: int
    ):
        """Adiciona cotas de imagem."""
        if not self.permission.is_admin(interaction.user, interaction.guild):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        economy = await self.db.get_economy(usuario.id)
        new_quota = economy.get("image_quota", 5) + quantidade
        
        await self.db.update_economy(usuario.id, image_quota=new_quota)
        
        await interaction.response.send_message(
            f"✅ **{quantidade}** cotas de imagem adicionadas para {usuario.mention}\n"
            f"Nova cota: **{new_quota}**",
            ephemeral=True
        )
    
    @admin_group.command(name="banir", description="Bloqueia um usuário de usar o bot")
    @app_commands.describe(
        usuario="Usuário a banir",
        motivo="Motivo do banimento"
    )
    async def admin_ban(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        motivo: Optional[str] = None
    ):
        """Bloqueia usuário."""
        if not self.permission.is_admin(interaction.user, interaction.guild):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        # Adicionar à lista de bloqueados
        blocked = self.config._config_data.get("permissions", {}).get("users", {}).get("blocked_ids", [])
        
        if usuario.id not in blocked:
            blocked.append(usuario.id)
            self.config._config_data["permissions"]["users"]["blocked_ids"] = blocked
            self.config.save()
        
        embed = discord.Embed(
            title="🚫 Usuário Banido",
            description=f"{usuario.mention} foi banido de usar o bot.",
            color=discord.Color.red()
        )
        
        if motivo:
            embed.add_field(name="Motivo", value=motivo, inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @admin_group.command(name="desbanir", description="Desbloqueia um usuário")
    @app_commands.describe(usuario="Usuário a desbanir")
    async def admin_unban(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member
    ):
        """Desbloqueia usuário."""
        if not self.permission.is_admin(interaction.user, interaction.guild):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        blocked = self.config._config_data.get("permissions", {}).get("users", {}).get("blocked_ids", [])
        
        if usuario.id in blocked:
            blocked.remove(usuario.id)
            self.config._config_data["permissions"]["users"]["blocked_ids"] = blocked
            self.config.save()
        
        await interaction.response.send_message(
            f"✅ {usuario.mention} foi desbanido.",
            ephemeral=True
        )
    
    @admin_group.command(name="backup", description="Cria backup manual do banco de dados")
    async def admin_backup(self, interaction: discord.Interaction):
        """Cria backup manual."""
        if not self.permission.is_admin(interaction.user, interaction.guild):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            backup_path = await self.db.create_backup()
            
            await interaction.followup.send(
                f"✅ Backup criado: `{backup_path}`",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Erro ao criar backup: {e}",
                ephemeral=True
            )
    
    @admin_group.command(name="stats", description="Estatísticas do servidor")
    async def admin_stats(self, interaction: discord.Interaction):
        """Mostra estatísticas do servidor."""
        if not self.permission.is_admin(interaction.user, interaction.guild):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        guild = interaction.guild
        
        # Contar canais ativos
        async with self.db._connection.execute(
            "SELECT COUNT(*) FROM channel_settings WHERE guild_id = ? AND is_active = 1",
            (guild.id,)
        ) as cursor:
            active_channels = (await cursor.fetchone())[0]
        
        # Total de mensagens
        async with self.db._connection.execute(
            "SELECT COUNT(*) FROM conversations WHERE guild_id = ?",
            (guild.id,)
        ) as cursor:
            total_messages = (await cursor.fetchone())[0]
        
        # Usuários ativos
        async with self.db._connection.execute(
            "SELECT COUNT(DISTINCT user_id) FROM conversations WHERE guild_id = ?",
            (guild.id,)
        ) as cursor:
            active_users = (await cursor.fetchone())[0]
        
        embed = discord.Embed(
            title=f"📊 Estatísticas de {guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Canais Ativos", value=active_channels, inline=True)
        embed.add_field(name="Mensagens Totais", value=total_messages, inline=True)
        embed.add_field(name="Usuários Ativos", value=active_users, inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @admin_group.command(name="limpar_historico", description="Limpa histórico de um canal")
    @app_commands.describe(canal="Canal para limpar")
    async def admin_clear_history(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel
    ):
        """Limpa histórico de um canal."""
        if not self.permission.is_admin(interaction.user, interaction.guild):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        await self.db.clear_conversation(canal.id)
        
        await interaction.response.send_message(
            f"✅ Histórico de {canal.mention} limpo.",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(AdminCommands(bot))
