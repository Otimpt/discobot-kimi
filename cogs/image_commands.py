"""
Comandos de Imagem
Geração de imagens com limites e quotas
"""

import logging
from datetime import datetime
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from core.config import Config
from database.manager import DatabaseManager
from providers.manager import ProviderManager
from utils.permission_checker import PermissionChecker, permission_denied_message

logger = logging.getLogger("discord-bot")


class ImageCommands(commands.Cog):
    """Comandos para geração de imagens."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config
        self.db: DatabaseManager = bot.db
        self.provider: ProviderManager = bot.provider
        self.permission = PermissionChecker(self.config)
    
    @app_commands.command(name="imagem", description="Gera uma imagem usando IA")
    @app_commands.describe(
        prompt="Descrição da imagem que você quer gerar",
        tamanho="Tamanho da imagem",
        qualidade="Qualidade da imagem"
    )
    @app_commands.choices(tamanho=[
        app_commands.Choice(name="Quadrada (1024x1024)", value="1024x1024"),
        app_commands.Choice(name="Paisagem (1792x1024)", value="1792x1024"),
        app_commands.Choice(name="Retrato (1024x1792)", value="1024x1792"),
    ])
    @app_commands.choices(qualidade=[
        app_commands.Choice(name="Padrão", value="standard"),
        app_commands.Choice(name="HD", value="hd"),
    ])
    async def image_generate(
        self,
        interaction: discord.Interaction,
        prompt: str,
        tamanho: Optional[app_commands.Choice[str]] = None,
        qualidade: Optional[app_commands.Choice[str]] = None
    ):
        """Gera uma imagem."""
        if not self.permission.check_permissions(interaction):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        # Verificar se geração de imagem está habilitada
        if not self.config.image_config.enabled:
            await interaction.response.send_message(
                "❌ Geração de imagens está desativada.",
                ephemeral=True
            )
            return
        
        # Verificar quota
        quota_status = await self.db.get_image_quota_status(interaction.user.id)
        
        if quota_status["remaining"] <= 0:
            embed = discord.Embed(
                title="🚫 Cota Esgotada",
                description="Você usou todas as suas gerações desta semana.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Como obter mais",
                value="Use `/loja comprar` para comprar mais gerações!",
                inline=False
            )
            embed.add_field(
                name="Reset em",
                value=quota_status["resets_in"],
                inline=True
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            # Gerar imagem
            size = tamanho.value if tamanho else "1024x1024"
            quality = qualidade.value if qualidade else "standard"
            
            image_url = await self.provider.generate_image(
                prompt=prompt,
                size=size,
                quality=quality
            )
            
            if not image_url:
                await interaction.followup.send(
                    "❌ Erro ao gerar imagem. Tente novamente mais tarde.",
                    ephemeral=True
                )
                return
            
            # Usar quota
            await self.db.check_and_use_image_quota(interaction.user.id)
            
            # Atualizar status
            quota_status = await self.db.get_image_quota_status(interaction.user.id)
            
            # Criar embed
            embed = discord.Embed(
                title="🎨 Imagem Gerada",
                description=f"**Prompt:** {prompt[:200]}{'...' if len(prompt) > 200 else ''}",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            embed.set_image(url=image_url)
            embed.set_footer(
                text=f"Por: {interaction.user.display_name} | "
                     f"Cotas restantes: {quota_status['remaining']}/{quota_status['quota']}"
            )
            
            await interaction.followup.send(embed=embed)
            
            # Registrar estatística
            await self.db.record_usage(
                user_id=interaction.user.id,
                guild_id=interaction.guild_id if interaction.guild else None,
                model="dall-e-3",
                images_generated=1
            )
            
        except Exception as e:
            logger.error(f"Erro ao gerar imagem: {e}")
            await interaction.followup.send(
                f"❌ Erro ao gerar imagem: {e}",
                ephemeral=True
            )
    
    @app_commands.command(name="cotas", description="Verifica suas cotas de imagem")
    async def image_quota(self, interaction: discord.Interaction):
        """Mostra status das cotas de imagem."""
        quota_status = await self.db.get_image_quota_status(interaction.user.id)
        
        embed = discord.Embed(
            title="🎨 Suas Cotas de Imagem",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Usadas esta semana",
            value=str(quota_status["weekly_used"]),
            inline=True
        )
        embed.add_field(
            name="Cota total",
            value=str(quota_status["quota"]),
            inline=True
        )
        embed.add_field(
            name="Restantes",
            value=str(quota_status["remaining"]),
            inline=True
        )
        embed.add_field(
            name="Reset em",
            value=quota_status["resets_in"],
            inline=True
        )
        
        if quota_status["remaining"] == 0:
            embed.add_field(
                name="💡 Dica",
                value="Use `/loja comprar` para adquirir mais gerações!",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(ImageCommands(bot))
