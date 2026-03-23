"""
Loja Aprimorada - Itens Especiais para Modo Interativo
Sistema de economia com itens criativos e efeitos especiais
"""

import logging
import random
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

import discord
from discord import app_commands
from discord.ext import commands

from core.config import Config
from database.manager import DatabaseManager
from utils.permission_checker import PermissionChecker

logger = logging.getLogger("discord-bot")


class ShopEnhanced(commands.Cog):
    """Loja com itens especiais para o modo interativo."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config
        self.db: DatabaseManager = bot.db
        self.permission = PermissionChecker(self.config)
        
        # Itens especiais do modo interativo
        self.special_items = {
            "possession_potion": {
                "name": "🧪 Poção de Possessão",
                "description": "Faz o membro ser possuído por outra persona por 15 minutos!",
                "cost": 200,
                "duration_minutes": 15,
                "effect": "possession",
                "category": "special",
                "requires_interactive": True
            },
            "strange_dream": {
                "name": "💭 Sonho Estranho",
                "description": "O membro terá um sonho bizarro e vai contar pra alguém!",
                "cost": 100,
                "effect": "strange_dream",
                "category": "special",
                "requires_interactive": True
            },
            "memory_wipe": {
                "name": "🧼 Esquecimento Parcial",
                "description": "O membro esquece algo aleatório e pode achar que esqueceu algo importante!",
                "cost": 150,
                "effect": "memory_wipe",
                "category": "special",
                "requires_interactive": True
            },
            "mood_swing": {
                "name": "🎭 Mudança de Humor",
                "description": "Altera o humor do membro para algo aleatório por 30 minutos!",
                "cost": 80,
                "duration_minutes": 30,
                "effect": "mood_swing",
                "category": "special",
                "requires_interactive": True
            },
            "energy_drink": {
                "name": "⚡ Energético",
                "description": "Deixa o membro hiperativo por 1 hora! Responde mais e com mais energia.",
                "cost": 120,
                "duration_minutes": 60,
                "effect": "energy_boost",
                "category": "special",
                "requires_interactive": True
            },
            "sleepy_tea": {
                "name": "🍵 Chá Sonolento",
                "description": "Deixa o membro sonolento por 45 minutos. Responde menos e mais devagar.",
                "cost": 90,
                "duration_minutes": 45,
                "effect": "sleepy",
                "category": "special",
                "requires_interactive": True
            },
            "truth_serum": {
                "name": "💉 Soro da Verdade",
                "description": "O membro fala mais sinceramente por 20 minutos!",
                "cost": 180,
                "duration_minutes": 20,
                "effect": "truth_serum",
                "category": "special",
                "requires_interactive": True
            },
            "confusion_spell": {
                "name": "✨ Feitiço de Confusão",
                "description": "O membro fica confuso e fala coisas sem sentido por 10 minutos!",
                "cost": 130,
                "duration_minutes": 10,
                "effect": "confusion",
                "category": "special",
                "requires_interactive": True
            },
            "love_potion": {
                "name": "💖 Poção do Amor",
                "description": "O membro fica mais carinhoso e atencioso por 25 minutos!",
                "cost": 160,
                "duration_minutes": 25,
                "effect": "love_potion",
                "category": "special",
                "requires_interactive": True
            },
            "grumpy_potion": {
                "name": "😤 Poção Rabugenta",
                "description": "O membro fica mal-humorado e reclamão por 20 minutos!",
                "cost": 110,
                "duration_minutes": 20,
                "effect": "grumpy",
                "category": "special",
                "requires_interactive": True
            },
            "philosopher_stone": {
                "name": "🧿 Pedra Filosofal",
                "description": "O membro fica filosófico e profundo por 30 minutos!",
                "cost": 140,
                "duration_minutes": 30,
                "effect": "philosopher",
                "category": "special",
                "requires_interactive": True
            },
            "time_warp": {
                "name": "🌀 Dobra do Tempo",
                "description": "O membro 'viaja no tempo' e fala como se fosse de outra época!",
                "cost": 190,
                "duration_minutes": 20,
                "effect": "time_warp",
                "category": "special",
                "requires_interactive": True
            },
            "image_quota_boost": {
                "name": "🎨 Pacote de Imagens",
                "description": "Adiciona +5 gerações de imagem à sua cota semanal!",
                "cost": 250,
                "effect": "add_image_quota",
                "effect_value": 5,
                "category": "utility",
                "requires_interactive": False
            },
            "memory_boost": {
                "name": "🧠 Boost de Memória",
                "description": "Aumenta a capacidade de memória do bot por 24 horas!",
                "cost": 300,
                "duration_minutes": 1440,
                "effect": "memory_boost",
                "category": "utility",
                "requires_interactive": False
            },
            "lucky_charm": {
                "name": "🍀 Amuleto da Sorte",
                "description": "Aumenta suas chances de ganhar na daily por 3 dias!",
                "cost": 500,
                "duration_minutes": 4320,
                "effect": "lucky_charm",
                "category": "utility",
                "requires_interactive": False
            }
        }
    
    # === Comandos da Loja ===
    
    loja_group = app_commands.Group(
        name="loja2",
        description="Loja de itens especiais (modo interativo)"
    )
    
    @loja_group.command(name="especiais", description="Lista itens especiais da loja")
    async def shop_special_items(self, interaction: discord.Interaction):
        """Lista itens especiais da loja."""
        embed = discord.Embed(
            title="🛍️ Loja de Itens Especiais",
            description="Itens mágicos para o modo interativo!",
            color=discord.Color.purple()
        )
        
        # Separar por categoria
        special_items = []
        utility_items = []
        
        for item_id, item_data in self.special_items.items():
            if item_data["category"] == "special":
                special_items.append((item_id, item_data))
            else:
                utility_items.append((item_id, item_data))
        
        # Adicionar itens especiais
        special_text = ""
        for item_id, item in special_items:
            special_text += f"**{item['name']}** - {item['cost']} {self.config.shop_config.currency_symbol}\n"
            special_text += f"*{item['description']}*\n\n"
        
        if special_text:
            embed.add_field(
                name="✨ Itens Mágicos (Modo Interativo)",
                value=special_text[:1024],
                inline=False
            )
        
        # Adicionar itens utilitários
        utility_text = ""
        for item_id, item in utility_items:
            utility_text += f"**{item['name']}** - {item['cost']} {self.config.shop_config.currency_symbol}\n"
            utility_text += f"*{item['description']}*\n\n"
        
        if utility_text:
            embed.add_field(
                name="🛠️ Itens Utilitários",
                value=utility_text[:1024],
                inline=False
            )
        
        # Mostrar saldo
        economy = await self.db.get_economy(interaction.user.id)
        embed.set_footer(
            text=f"Seu saldo: {economy['tokens']} {self.config.shop_config.currency_symbol}"
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @loja_group.command(name="comprar", description="Compra um item especial")
    @app_commands.describe(item="ID do item a comprar")
    @app_commands.autocomplete(item=lambda interaction, current: [
        app_commands.Choice(
            name=f"{data['name']} - {data['cost']} {interaction.client.config.shop_config.currency_symbol}",
            value=item_id
        )
        for item_id, data in interaction.client.get_cog("ShopEnhanced").special_items.items()
        if current.lower() in data['name'].lower() or current.lower() in item_id.lower()
    ][:25])
    async def shop_buy_special(
        self,
        interaction: discord.Interaction,
        item: str
    ):
        """Compra um item especial."""
        if item not in self.special_items:
            await interaction.response.send_message(
                f"❌ Item '{item}' não encontrado.",
                ephemeral=True
            )
            return
        
        item_data = self.special_items[item]
        cost = item_data["cost"]
        
        # Verificar se requer modo interativo
        if item_data.get("requires_interactive", False):
            # Verificar se o canal está em modo interativo
            channel_settings = await self.db.get_channel_settings(interaction.channel_id)
            if channel_settings.get("mode") != "interactive":
                await interaction.response.send_message(
                    "❌ Este item só funciona no **modo interativo**!\n"
                    "Use `/config modo interactive` para ativar.",
                    ephemeral=True
                )
                return
        
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
        success = await self._process_special_purchase(
            interaction,
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
                    json.dumps({
                        "duration": item_data.get("duration_minutes"),
                        "value": item_data.get("effect_value")
                    }),
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
            
            if item_data.get("duration_minutes"):
                embed.add_field(
                    name="Duração",
                    value=f"{item_data['duration_minutes']} minutos",
                    inline=True
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                "❌ Erro ao processar compra. Tente novamente.",
                ephemeral=True
            )
    
    @loja_group.command(name="efeitos", description="Mostra efeitos ativos no canal")
    async def shop_active_effects(self, interaction: discord.Interaction):
        """Mostra efeitos ativos no canal."""
        effects = await self._get_active_effects(interaction.channel_id)
        
        if not effects:
            await interaction.response.send_message(
                "📭 Nenhum efeito ativo neste canal no momento.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="✨ Efeitos Ativos",
            description="Itens mágicos em funcionamento neste canal:",
            color=discord.Color.purple()
        )
        
        for effect in effects:
            time_left = effect["expires_at"] - datetime.now()
            minutes_left = int(time_left.total_seconds() / 60)
            
            embed.add_field(
                name=effect["item_name"],
                value=f"Ativo por mais **{minutes_left} minutos**\n"
                      f"*Comprado por {effect['buyer_name']}*",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def _process_special_purchase(
        self,
        interaction: discord.Interaction,
        item_id: str,
        item_data: dict
    ) -> bool:
        """Processa a compra de um item especial."""
        effect = item_data.get("effect")
        
        try:
            if effect == "possession":
                return await self._apply_possession_effect(
                    interaction, item_data
                )
            
            elif effect == "strange_dream":
                return await self._apply_strange_dream_effect(
                    interaction, item_data
                )
            
            elif effect == "memory_wipe":
                return await self._apply_memory_wipe_effect(
                    interaction, item_data
                )
            
            elif effect in ["mood_swing", "energy_boost", "sleepy", 
                           "truth_serum", "confusion", "love_potion", 
                           "grumpy", "philosopher", "time_warp"]:
                return await self._apply_temporary_effect(
                    interaction, item_id, item_data
                )
            
            elif effect == "add_image_quota":
                economy = await self.db.get_economy(interaction.user.id)
                new_quota = economy.get("image_quota", 5) + item_data.get("effect_value", 5)
                await self.db.update_economy(interaction.user.id, image_quota=new_quota)
                return True
            
            elif effect == "memory_boost":
                return await self._apply_memory_boost_effect(
                    interaction, item_data
                )
            
            elif effect == "lucky_charm":
                return await self._apply_lucky_charm_effect(
                    interaction, item_data
                )
            
            return True
        
        except Exception as e:
            logger.error(f"Erro ao processar compra especial: {e}")
            return False
    
    async def _apply_possession_effect(
        self,
        interaction: discord.Interaction,
        item_data: dict
    ) -> bool:
        """Aplica efeito de possessão."""
        # Obter personas disponíveis
        personas = await self.db.list_personas(interaction.guild_id)
        
        if not personas:
            await interaction.response.send_message(
                "❌ Não há personas disponíveis para possessão!",
                ephemeral=True
            )
            return False
        
        # Escolher persona aleatória (excluindo a atual se houver)
        persona = random.choice(personas)
        duration = item_data.get("duration_minutes", 15)
        
        # Registrar efeito no banco
        expires_at = datetime.now() + timedelta(minutes=duration)
        await self.db._connection.execute(
            """INSERT INTO active_effects 
               (user_id, channel_id, effect_type, effect_data, expires_at, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                interaction.user.id,
                interaction.channel_id,
                "possession",
                json.dumps({
                    "persona_name": persona["name"],
                    "persona_prompt": persona["system_prompt"],
                    "buyer_id": interaction.user.id,
                    "buyer_name": interaction.user.display_name
                }),
                expires_at,
                datetime.now()
            )
        )
        await self.db._connection.commit()
        
        # Notificar no canal
        embed = discord.Embed(
            title="🧪 POÇÃO DE POSSESSÃO ATIVADA!",
            description=f"**{interaction.user.display_name}** usou uma Poção de Possessão!",
            color=discord.Color.purple()
        )
        embed.add_field(
            name="👻 Possessão",
            value=f"O membro foi possuído por **{persona['name']}**!",
            inline=False
        )
        embed.add_field(
            name="⏱️ Duração",
            value=f"{duration} minutos",
            inline=True
        )
        embed.set_footer(text="Algo estranho está acontecendo... 👀")
        
        await interaction.channel.send(embed=embed)
        
        # Agendar fim da possessão
        self.bot.loop.create_task(
            self._schedule_possession_end(interaction.channel_id, duration, persona["name"])
        )
        
        return True
    
    async def _apply_strange_dream_effect(
        self,
        interaction: discord.Interaction,
        item_data: dict
    ) -> bool:
        """Aplica efeito de sonho estranho."""
        # Lista de sonhos estranhos
        strange_dreams = [
            "Você sonhou que era um pinguim tentando voar...",
            "No seu sonho, você era um astronauta em Marte fazendo churrasco...",
            "Você sonhou que estava numa festa de aniversário de um hamster gigante...",
            "No sonho, você era um detetive investigando o mistério do biscoito desaparecido...",
            "Você sonhou que estava numa ilha deserta com apenas um celular sem bateria...",
            "No seu sonho, você era um chef de cozinha que só sabia fazer sanduíche de queijo...",
            "Você sonhou que estava num torneio de xadrez contra um gato muito inteligente...",
            "No sonho, você era um super-herói cujo poder era fazer pipoca com a mente...",
            "Você sonhou que estava num mundo onde todos falavam em rimas...",
            "No seu sonho, você era um pirata procurando tesouro no quintal da vizinha...",
            "Você sonhou que estava num reality show de plantas suculentas...",
            "No sonho, você era um cientista que descobriu que a gravidade era só uma sugestão...",
            "Você sonhou que estava numa maratona de filme com um sloth muito ansioso...",
            "No seu sonho, você era um músico famoso que tocava colher de pau...",
            "Você sonhou que estava num jantar formal onde todo mundo usava pijama..."
        ]
        
        dream = random.choice(strange_dreams)
        
        # Registrar efeito
        await self.db._connection.execute(
            """INSERT INTO active_effects 
               (user_id, channel_id, effect_type, effect_data, expires_at, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                interaction.user.id,
                interaction.channel_id,
                "strange_dream",
                json.dumps({
                    "dream": dream,
                    "buyer_id": interaction.user.id,
                    "buyer_name": interaction.user.display_name
                }),
                datetime.now() + timedelta(hours=1),
                datetime.now()
            )
        )
        await self.db._connection.commit()
        
        # O bot vai contar o sonho em breve
        self.bot.loop.create_task(
            self._schedule_dream_telling(interaction.channel_id, dream)
        )
        
        return True
    
    async def _apply_memory_wipe_effect(
        self,
        interaction: discord.Interaction,
        item_data: dict
    ) -> bool:
        """Aplica efeito de esquecimento."""
        # Tipos de esquecimento
        forget_types = [
            "o que estava fazendo ontem à noite",
            "o nome daquele filme que todo mundo fala",
            "por que entrou nesta sala",
            "o que ia falar a seguir",
            "onde deixou as chaves (mas não usa chaves... estranho)",
            "o nome do usuário que acabou de falar com você",
            "qual era a pergunta que fizeram",
            "o que almoçou hoje",
            "por que está rindo",
            "o que estava procurando"
        ]
        
        forgotten = random.choice(forget_types)
        
        # Registrar efeito
        await self.db._connection.execute(
            """INSERT INTO active_effects 
               (user_id, channel_id, effect_type, effect_data, expires_at, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                interaction.user.id,
                interaction.channel_id,
                "memory_wipe",
                json.dumps({
                    "forgotten": forgotten,
                    "buyer_id": interaction.user.id,
                    "buyer_name": interaction.user.display_name
                }),
                datetime.now() + timedelta(hours=2),
                datetime.now()
            )
        )
        await self.db._connection.commit()
        
        # O bot vai demonstrar esquecimento em breve
        self.bot.loop.create_task(
            self._schedule_forgetfulness(interaction.channel_id, forgotten)
        )
        
        return True
    
    async def _apply_temporary_effect(
        self,
        interaction: discord.Interaction,
        item_id: str,
        item_data: dict
    ) -> bool:
        """Aplica um efeito temporário no membro interativo."""
        duration = item_data.get("duration_minutes", 30)
        effect = item_data["effect"]
        
        expires_at = datetime.now() + timedelta(minutes=duration)
        
        await self.db._connection.execute(
            """INSERT INTO active_effects 
               (user_id, channel_id, effect_type, effect_data, expires_at, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                interaction.user.id,
                interaction.channel_id,
                effect,
                json.dumps({
                    "item_id": item_id,
                    "item_name": item_data["name"],
                    "buyer_id": interaction.user.id,
                    "buyer_name": interaction.user.display_name
                }),
                expires_at,
                datetime.now()
            )
        )
        await self.db._connection.commit()
        
        # Notificar no canal
        notification = self._get_effect_notification(effect, item_data)
        if notification:
            await interaction.channel.send(notification)
        
        return True
    
    def _get_effect_notification(self, effect: str, item_data: dict) -> Optional[str]:
        """Retorna mensagem de notificação para um efeito."""
        notifications = {
            "mood_swing": (
                f"🎭 **Mudança de Humor!**\n\n"
                f"O membro está se sentindo... diferente.\n"
                f"*Duração: {item_data.get('duration_minutes', 30)} minutos*"
            ),
            "energy_boost": (
                f"⚡ **ENERGÉTICO CONSUMIDO!**\n\n"
                f"O membro está HIPERATIVO! 🚀\n"
                f"*Duração: {item_data.get('duration_minutes', 60)} minutos*"
            ),
            "sleepy": (
                f"🍵 **Chá Sonolento!**\n\n"
                f"O membro ficou com **sono**... 😴\n"
                f"Por **{item_data.get('duration_minutes', 45)} minutos** ele vai:\n"
                f"• Responder menos\n"
                f"• Usar mais '...' nas frases\n"
                f"• Perguntar 'que horas são?'\n\n"
                f"*Hora do cochilo...* 💤"
            ),
            "truth_serum": (
                f"💉 **SORO DA VERDADE!**\n\n"
                f"O membro vai falar a **verdade** por **{item_data.get('duration_minutes', 20)} minutos**!\n"
                f"*Sem filtros, sem mentiras!* 😤"
            ),
            "confusion": (
                f"✨ **CONFUSÃO!**\n\n"
                f"O membro está **confuso**! 🤪\n"
                f"Por **{item_data.get('duration_minutes', 10)} minutos** ele vai falar coisas sem sentido!"
            ),
            "love_potion": (
                f"💖 **POÇÃO DO AMOR!**\n\n"
                f"O membro está cheio de **amor**! 🥰\n"
                f"Por **{item_data.get('duration_minutes', 25)} minutos** ele vai ser super carinhoso!"
            ),
            "grumpy": (
                f"😤 **POÇÃO RABUGENTA!**\n\n"
                f"O membro está de **mau humor**! 😠\n"
                f"Por **{item_data.get('duration_minutes', 20)} minutos** ele vai reclamar de tudo!"
            ),
            "philosopher": (
                f"🧿 **PEDRA FILOSOFAL!**\n\n"
                f"O membro está **filosófico**! 🤔\n"
                f"Por **{item_data.get('duration_minutes', 30)} minutos** ele vai falar coisas profundas!"
            ),
            "time_warp": (
                f"🌀 **DOBRA DO TEMPO!**\n\n"
                f"O membro 'viajou no tempo'! ⏰\n"
                f"Por **{item_data.get('duration_minutes', 20)} minutos** ele fala como se fosse de outra época!"
            )
        }
        
        return notifications.get(effect)
    
    async def _apply_memory_boost_effect(
        self,
        interaction: discord.Interaction,
        item_data: dict
    ) -> bool:
        """Aplica boost de memória."""
        duration = item_data.get("duration_minutes", 1440)
        expires_at = datetime.now() + timedelta(minutes=duration)
        
        await self.db._connection.execute(
            """INSERT INTO active_effects 
               (user_id, channel_id, effect_type, effect_data, expires_at, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                interaction.user.id,
                interaction.channel_id,
                "memory_boost",
                json.dumps({
                    "multiplier": 2,
                    "buyer_id": interaction.user.id,
                    "buyer_name": interaction.user.display_name
                }),
                expires_at,
                datetime.now()
            )
        )
        await self.db._connection.commit()
        
        await interaction.channel.send(
            f"🧠 **Boost de Memória Ativado!**\n"
            f"A capacidade de memória do bot foi duplicada por **{duration // 60} horas**!"
        )
        
        return True
    
    async def _apply_lucky_charm_effect(
        self,
        interaction: discord.Interaction,
        item_data: dict
    ) -> bool:
        """Aplica amuleto da sorte."""
        duration = item_data.get("duration_minutes", 4320)
        expires_at = datetime.now() + timedelta(minutes=duration)
        
        await self.db._connection.execute(
            """INSERT INTO active_effects 
               (user_id, channel_id, effect_type, effect_data, expires_at, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                interaction.user.id,
                interaction.channel_id,
                "lucky_charm",
                json.dumps({
                    "bonus": 1.5,
                    "buyer_id": interaction.user.id,
                    "buyer_name": interaction.user.display_name
                }),
                expires_at,
                datetime.now()
            )
        )
        await self.db._connection.commit()
        
        await interaction.channel.send(
            f"🍀 **Amuleto da Sorte Ativado!**\n"
            f"{interaction.user.display_name} terá **50% mais sorte** na daily por **3 dias**!"
        )
        
        return True
    
    # === Tarefas Agendadas ===
    
    async def _schedule_possession_end(
        self,
        channel_id: int,
        duration_minutes: int,
        persona_name: str
    ):
        """Agenda o fim da possessão."""
        await discord.utils.sleep_until(
            datetime.now() + timedelta(minutes=duration_minutes)
        )
        
        channel = self.bot.get_channel(channel_id)
        if channel:
            # Chance de não lembrar
            if random.random() < 0.3:
                await channel.send(
                    f"👻 **A possessão terminou...**\n\n"
                    f"*O membro pisca confuso*\n"
                    f"'Ué... o que aconteceu? Sinto como se tivesse perdido alguns minutos...'"
                )
            else:
                await channel.send(
                    f"✨ **A possessão terminou!**\n\n"
                    f"O membro voltou ao normal. {persona_name} foi embora...\n"
                    f"*Ele parece ter uma memória estranha do que aconteceu* 👀"
                )
        
        # Limpar efeito do banco
        await self.db._connection.execute(
            "DELETE FROM active_effects WHERE channel_id = ? AND effect_type = ?",
            (channel_id, "possession")
        )
        await self.db._connection.commit()
    
    async def _schedule_dream_telling(self, channel_id: int, dream: str):
        """Agenda o membro contando o sonho."""
        # Esperar entre 5 e 15 minutos
        wait_minutes = random.randint(5, 15)
        await discord.utils.sleep_until(
            datetime.now() + timedelta(minutes=wait_minutes)
        )
        
        channel = self.bot.get_channel(channel_id)
        if channel:
            intros = [
                "*bocejo* Cara... tive um sonho tão estranho...",
                "Vocês não vão acreditar no sonho que eu tive!",
                "Gente, acabei de acordar de um sonho MUITO bizarro...",
                "*esfrega os olhos* Sonhei uma coisa muito doida...",
                "Nossa, tive um sonho tão estranho que preciso contar!"
            ]
            
            intro = random.choice(intros)
            
            await channel.send(
                f"💭 **{intro}**\n\n"
                f"{dream}\n\n"
                f"*O que vocês acham que significa?* 🤔"
            )
    
    async def _schedule_forgetfulness(self, channel_id: int, forgotten: str):
        """Agenda o membro demonstrando esquecimento."""
        # Esperar entre 3 e 10 minutos
        wait_minutes = random.randint(3, 10)
        await discord.utils.sleep_until(
            datetime.now() + timedelta(minutes=wait_minutes)
        )
        
        channel = self.bot.get_channel(channel_id)
        if channel:
            phrases = [
                f"*bate na cabeça* Espera... eu esqueci {forgotten}...",
                f"Nossa, deixa eu te falar uma coisa... ah não, esqueci. Esqueci {forgotten} 😅",
                f"Tem algo na ponta da língua... ah! Esqueci {forgotten}!",
                f"*olha confuso* Eu tinha certeza que sabia... mas esqueci {forgotten}",
                f"Gente, não é possível... esqueci {forgotten}! Tô ficando louco?"
            ]
            
            # Chance de achar que esqueceu algo importante
            if random.random() < 0.3:
                phrases.append(
                    f"*olha preocupado* Acho que esqueci algo importante... "
                    f"algo sobre {forgotten}... mas não consigo lembrar o quê..."
                )
            
            phrase = random.choice(phrases)
            await channel.send(phrase)
    
    async def _get_active_effects(self, channel_id: int) -> List[Dict[str, Any]]:
        """Obtém efeitos ativos em um canal."""
        async with self.db._connection.execute(
            """SELECT * FROM active_effects 
               WHERE channel_id = ? AND expires_at > ?
               ORDER BY expires_at""",
            (channel_id, datetime.now())
        ) as cursor:
            rows = await cursor.fetchall()
            effects = []
            for row in rows:
                effect_data = json.loads(row["effect_data"])
                effects.append({
                    "effect_type": row["effect_type"],
                    "item_name": effect_data.get("item_name", row["effect_type"]),
                    "buyer_name": effect_data.get("buyer_name", "Desconhecido"),
                    "expires_at": datetime.fromisoformat(row["expires_at"])
                    if isinstance(row["expires_at"], str) else row["expires_at"]
                })
            return effects
    
    # === Eventos Aleatórios ===
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Verifica eventos aleatórios em mensagens."""
        if message.author.bot:
            return
        
        # Verificar se é modo interativo
        channel_settings = await self.db.get_channel_settings(message.channel.id)
        if channel_settings.get("mode") != "interactive":
            return
        
        # Chance de eventos aleatórios (muito rara)
        if random.random() < 0.001:  # 0.1% de chance
            await self._trigger_random_event(message)
    
    async def _trigger_random_event(self, message: discord.Message):
        """Dispara um evento aleatório."""
        events = [
            self._random_possession,
            self._random_strange_dream,
            self._random_memory_hint
        ]
        
        event = random.choice(events)
        await event(message)
    
    async def _random_possession(self, message: discord.Message):
        """Possessão aleatória (muito rara)."""
        personas = await self.db.list_personas(message.guild.id)
        if not personas:
            return
        
        persona = random.choice(personas)
        
        await message.channel.send(
            f"👻 **EVENTO RARO!**\n\n"
            f"*O membro estremece de repente*\n"
            f"'Quem... quem sou eu? Por um momento me senti como {persona['name']}...'\n\n"
            f"*Ele parece confuso, mas logo volta ao normal*"
        )
    
    async def _random_strange_dream(self, message: discord.Message):
        """Sonho estranho aleatório."""
        strange_dreams = [
            "um pinguim astronauta",
            "um mundo feito de chocolate",
            "um gato que falava português",
            "uma festa de aniversário para uma planta",
            "um carro que voava como avião"
        ]
        
        dream = random.choice(strange_dreams)
        
        await message.channel.send(
            f"💭 *O membro parece distraído*\n\n"
            f"'Nossa... acabei de lembrar de um sonho que tive... "
            f"sonhei com {dream}... que estranho, né?'"
        )
    
    async def _random_memory_hint(self, message: discord.Message):
        """Dica de memória esquecida."""
        await message.channel.send(
            f"🤔 *O membro franze a testa*\n\n"
            f"'Tem algo que eu deveria lembrar... algo importante... "
            f"mas não consigo... será que é sobre você?'")


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(ShopEnhanced(bot))
