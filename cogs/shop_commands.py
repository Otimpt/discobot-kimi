"""
Comandos da Loja
Sistema de economia e compras
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


class ShopCommands(commands.Cog):
    """Comandos da loja do bot."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config
        self.db: DatabaseManager = bot.db
        self.permission = PermissionChecker(self.config)
    
    loja_group = app_commands.Group(
        name="loja",
        description="Loja de itens e tokens"
    )
    
    @loja_group.command(name="itens", description="Lista todos os itens disponíveis")
    async def shop_items(self, interaction: discord.Interaction):
        """Lista itens da loja."""
        items = self.config.shop_config.items
        
        if not items:
            await interaction.response.send_message(
                "📭 A loja está vazia no momento.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🛒 Loja de Itens",
            description=f"Compre itens usando {self.config.shop_config.currency_symbol} {self.config.shop_config.currency_name}",
            color=discord.Color.gold()
        )
        
        for item_id, item_data in items.items():
            embed.add_field(
                name=f"{item_data['name']} - {item_data['cost']} {self.config.shop_config.currency_symbol}",
                value=f"{item_data['description']}\n"
                      f"*Efeito: {item_data['effect']}*",
                inline=False
            )
        
        # Mostrar saldo
        economy = await self.db.get_economy(interaction.user.id)
        embed.set_footer(
            text=f"Seu saldo: {economy['tokens']} {self.config.shop_config.currency_symbol}"
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @loja_group.command(name="saldo", description="Verifica seu saldo de tokens")
    async def shop_balance(self, interaction: discord.Interaction):
        """Mostra saldo do usuário."""
        economy = await self.db.get_economy(interaction.user.id)
        quota = await self.db.get_image_quota_status(interaction.user.id)
        
        embed = discord.Embed(
            title="💰 Seu Saldo",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name=self.config.shop_config.currency_name,
            value=f"{self.config.shop_config.currency_symbol} {economy['tokens']}",
            inline=True
        )
        embed.add_field(
            name="Cota de Imagens",
            value=f"{quota['remaining']} restantes",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @loja_group.command(name="comprar", description="Compra um item da loja")
    @app_commands.describe(item="ID do item a comprar")
    @app_commands.autocomplete(item=lambda interaction, current: [
        app_commands.Choice(
            name=f"{data['name']} - {data['cost']} {interaction.client.config.shop_config.currency_symbol}",
            value=item_id
        )
        for item_id, data in interaction.client.config.shop_config.items.items()
        if current.lower() in data['name'].lower() or current.lower() in item_id.lower()
    ][:25])
    async def shop_buy(
        self,
        interaction: discord.Interaction,
        item: str
    ):
        """Compra um item."""
        items = self.config.shop_config.items
        
        if item not in items:
            await interaction.response.send_message(
                f"❌ Item '{item}' não encontrado.",
                ephemeral=True
            )
            return
        
        item_data = items[item]
        cost = item_data["cost"]
        
        # Verificar saldo
        economy = await self.db.get_economy(interaction.user.id)
        
        if economy["tokens"] < cost:
            await interaction.response.send_message(
                f"❌ Saldo insuficiente!\n"
                f"Custo: {cost} {self.config.shop_config.currency_symbol}\n"
                f"Seu saldo: {economy['tokens']} {self.config.shop_config.currency_symbol}",
                ephemeral=True
            )
            return
        
        # Processar compra
        success = await self._process_purchase(
            interaction.user.id,
            item,
            item_data
        )
        
        if success:
            # Remover tokens
            await self.db.remove_tokens(interaction.user.id, cost)
            
            # Registrar transação
            await self.db._connection.execute(
                """INSERT INTO shop_transactions 
                   (user_id, item_id, item_name, cost, effect_type, effect_value, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    interaction.user.id,
                    item,
                    item_data["name"],
                    cost,
                    item_data["effect"],
                    str(item_data.get("effect_value", "")),
                    datetime.now()
                )
            )
            await self.db._connection.commit()
            
            embed = discord.Embed(
                title="✅ Compra Realizada!",
                description=f"Você comprou **{item_data['name']}**!",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Custo",
                value=f"{cost} {self.config.shop_config.currency_symbol}",
                inline=True
            )
            
            new_balance = economy["tokens"] - cost
            embed.add_field(
                name="Novo Saldo",
                value=f"{new_balance} {self.config.shop_config.currency_symbol}",
                inline=True
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                "❌ Erro ao processar compra. Tente novamente.",
                ephemeral=True
            )
    
    @loja_group.command(name="daily", description="Resgata sua recompensa diária")
    async def shop_daily(self, interaction: discord.Interaction):
        """Resgata recompensa diária."""
        # Verificar se já resgatou hoje
        async with self.db._connection.execute(
            """SELECT created_at FROM shop_transactions 
               WHERE user_id = ? AND item_id = 'daily_reward' 
               AND DATE(created_at) = DATE('now')""",
            (interaction.user.id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                await interaction.response.send_message(
                    "⏰ Você já resgatou sua recompensa diária hoje!\n"
                    "Volte amanhã para mais tokens.",
                    ephemeral=True
                )
                return
        
        # Dar recompensa
        reward = 20
        await self.db.add_tokens(interaction.user.id, reward)
        
        # Registrar
        await self.db._connection.execute(
            """INSERT INTO shop_transactions 
               (user_id, item_id, item_name, cost, effect_type, effect_value, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                interaction.user.id,
                "daily_reward",
                "Recompensa Diária",
                0,
                "add_tokens",
                str(reward),
                datetime.now()
            )
        )
        await self.db._connection.commit()
        
        economy = await self.db.get_economy(interaction.user.id)
        
        embed = discord.Embed(
            title="🎁 Recompensa Diária!",
            description=f"Você recebeu **{reward}** {self.config.shop_config.currency_symbol}!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Saldo Atual",
            value=f"{economy['tokens']} {self.config.shop_config.currency_symbol}",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @loja_group.command(name="transferir", description="Transfere tokens para outro usuário")
    @app_commands.describe(
        usuario="Usuário para transferir",
        quantidade="Quantidade de tokens"
    )
    async def shop_transfer(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        quantidade: int
    ):
        """Transfere tokens."""
        if quantidade <= 0:
            await interaction.response.send_message(
                "❌ Quantidade inválida.",
                ephemeral=True
            )
            return
        
        if usuario.id == interaction.user.id:
            await interaction.response.send_message(
                "❌ Você não pode transferir para si mesmo.",
                ephemeral=True
            )
            return
        
        # Verificar saldo
        economy = await self.db.get_economy(interaction.user.id)
        
        if economy["tokens"] < quantidade:
            await interaction.response.send_message(
                f"❌ Saldo insuficiente!\n"
                f"Você tem: {economy['tokens']} {self.config.shop_config.currency_symbol}",
                ephemeral=True
            )
            return
        
        # Transferir
        await self.db.remove_tokens(interaction.user.id, quantidade)
        await self.db.add_tokens(usuario.id, quantidade)
        
        embed = discord.Embed(
            title="💸 Transferência Realizada",
            description=f"**{quantidade}** {self.config.shop_config.currency_symbol} "
                       f"transferidos para {usuario.mention}!",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)
    
    async def _process_purchase(
        self,
        user_id: int,
        item_id: str,
        item_data: dict
    ) -> bool:
        """Processa o efeito de uma compra."""
        effect = item_data.get("effect")
        effect_value = item_data.get("effect_value")
        
        try:
            if effect == "add_image_quota":
                economy = await self.db.get_economy(user_id)
                new_quota = economy.get("image_quota", 5) + effect_value
                await self.db.update_economy(user_id, image_quota=new_quota)
                return True
            
            elif effect == "unlock_feature":
                # Implementar desbloqueio de features
                return True
            
            elif effect == "boost_memory":
                # Implementar boost de memória
                return True
            
            return True
        except Exception as e:
            logger.error(f"Erro ao processar compra: {e}")
            return False
    
    @app_commands.command(name="top", description="Mostra o ranking de tokens")
    async def shop_leaderboard(self, interaction: discord.Interaction):
        """Mostra ranking de tokens."""
        async with self.db._connection.execute(
            """SELECT user_id, tokens FROM economy 
               ORDER BY tokens DESC LIMIT 10"""
        ) as cursor:
            rows = await cursor.fetchall()
        
        if not rows:
            await interaction.response.send_message(
                "📭 Nenhum dado disponível.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f"🏆 Ranking de {self.config.shop_config.currency_name}",
            color=discord.Color.gold()
        )
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, row in enumerate(rows):
            user = self.bot.get_user(row["user_id"])
            user_name = user.display_name if user else f"Usuário {row['user_id']}"
            
            medal = medals[i] if i < 3 else f"{i+1}."
            embed.add_field(
                name=f"{medal} {user_name}",
                value=f"{row['tokens']} {self.config.shop_config.currency_symbol}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(ShopCommands(bot))
