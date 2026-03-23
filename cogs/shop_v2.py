"""
Loja V2 - Sistema Completo com Raridade, Loja Rotativa e Inventário
"""

import logging
import random
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum

import discord
from discord import app_commands
from discord.ext import commands, tasks

from core.config import Config
from database.manager import DatabaseManager
from utils.permission_checker import PermissionChecker

logger = logging.getLogger("discord-bot")


class Rarity(Enum):
    """Raridade dos itens."""
    COMMON = ("Comum", "🟢", 0.60)
    RARE = ("Raro", "🔵", 0.30)
    EPIC = ("Épico", "🟣", 0.09)
    LEGENDARY = ("Lendário", "🟡", 0.01)
    
    def __init__(self, label: str, emoji: str, chance: float):
        self.label = label
        self.emoji = emoji
        self.chance = chance


class ItemCategory(Enum):
    """Categorias de itens."""
    TRANSFORMATION = "transformacao"  # Muda comportamento do bot
    UTILITY = "utilitario"            # Utilitários
    CONSUMABLE = "consumivel"         # Consumíveis imediatos
    PERMANENT = "permanente"          # Efeitos permanentes


class ShopItem:
    """Representa um item da loja."""
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        cost: int,
        rarity: Rarity,
        category: ItemCategory,
        effect: str,
        duration_minutes: Optional[int] = None,
        effect_value: Any = None,
        usable: bool = True,  # Se vai para o inventário
        stackable: bool = False,
        max_stack: int = 1
    ):
        self.id = id
        self.name = name
        self.description = description
        self.cost = cost
        self.rarity = rarity
        self.category = category
        self.effect = effect
        self.duration_minutes = duration_minutes
        self.effect_value = effect_value
        self.usable = usable
        self.stackable = stackable
        self.max_stack = max_stack
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "cost": self.cost,
            "rarity": self.rarity.name,
            "category": self.category.value,
            "effect": self.effect,
            "duration_minutes": self.duration_minutes,
            "effect_value": self.effect_value,
            "usable": self.usable,
            "stackable": self.stackable,
            "max_stack": self.max_stack
        }


class ShopV2(commands.Cog):
    """Sistema de loja completo V2."""
    
    # === ITENS FIXOS (sempre disponíveis) ===
    FIXED_ITEMS = {
        # Geração de Imagem
        "image_gen_1": ShopItem(
            id="image_gen_1",
            name="🎨 Geração de Imagem x1",
            description="Adiciona 1 geração de imagem à sua cota semanal",
            cost=400,
            rarity=Rarity.COMMON,
            category=ItemCategory.CONSUMABLE,
            effect="add_image_quota",
            effect_value=1,
            usable=False
        ),
        "image_gen_3": ShopItem(
            id="image_gen_3",
            name="🎨 Geração de Imagem x3",
            description="Adiciona 3 gerações de imagem à sua cota semanal",
            cost=1000,
            rarity=Rarity.RARE,
            category=ItemCategory.CONSUMABLE,
            effect="add_image_quota",
            effect_value=3,
            usable=False
        ),
        
        # Boost de Memória
        "memory_boost": ShopItem(
            id="memory_boost",
            name="🧠 Boost de Memória",
            description="Dobra a capacidade de memória do bot por 24 horas",
            cost=800,
            rarity=Rarity.RARE,
            category=ItemCategory.CONSUMABLE,
            effect="memory_boost",
            duration_minutes=1440,
            usable=False
        ),
        
        # Amuleto da Sorte
        "lucky_charm": ShopItem(
            id="lucky_charm",
            name="🍀 Amuleto da Sorte",
            description="Aumenta em 50% suas chances na daily por 3 dias",
            cost=1200,
            rarity=Rarity.EPIC,
            category=ItemCategory.CONSUMABLE,
            effect="lucky_charm",
            duration_minutes=4320,
            usable=False
        ),
        
        # Resumo Premium
        "premium_summary": ShopItem(
            id="premium_summary",
            name="📋 Resumo Premium",
            description="Bot faz resumo dos últimos 1000 mensagens do canal",
            cost=1500,
            rarity=Rarity.EPIC,
            category=ItemCategory.CONSUMABLE,
            effect="premium_summary",
            usable=False
        ),
        
        # Backup de Memória
        "memory_backup": ShopItem(
            id="memory_backup",
            name="💾 Backup de Memória",
            description="Salva todas as memórias atuais em um arquivo exportável",
            cost=2000,
            rarity=Rarity.EPIC,
            category=ItemCategory.CONSUMABLE,
            effect="memory_backup",
            usable=False
        ),
        
        # Análise de Chat
        "chat_analysis": ShopItem(
            id="chat_analysis",
            name="📊 Análise de Chat",
            description="Bot analisa o humor, temas e estatísticas do servidor",
            cost=2500,
            rarity=Rarity.LEGENDARY,
            category=ItemCategory.CONSUMABLE,
            effect="chat_analysis",
            usable=False
        ),
    }
    
    # === ITENS ROTATIVOS (mudam a cada 3 dias) ===
    ROTATING_ITEMS = {
        # Transformações de Personalidade
        "old_man_cane": ShopItem(
            id="old_man_cane",
            name="🦯 Bengala de Velho",
            description="Bot fica reclamando 'no meu tempo...' por 30 minutos",
            cost=500,
            rarity=Rarity.COMMON,
            category=ItemCategory.TRANSFORMATION,
            effect="old_man",
            duration_minutes=30,
            usable=True
        ),
        "clown_mask": ShopItem(
            id="clown_mask",
            name="🎭 Máscara do Palhaço",
            description="Bot fica fazendo piadas e sendo engraçado por 30 minutos",
            cost=450,
            rarity=Rarity.COMMON,
            category=ItemCategory.TRANSFORMATION,
            effect="clown",
            duration_minutes=30,
            usable=True
        ),
        "nerd_glasses": ShopItem(
            id="nerd_glasses",
            name="🤓 Óculos de Nerd",
            description="Bot fala com fatos interessantes e curiosidades por 30 minutos",
            cost=400,
            rarity=Rarity.COMMON,
            category=ItemCategory.TRANSFORMATION,
            effect="nerd",
            duration_minutes=30,
            usable=True
        ),
        "crystal_ball": ShopItem(
            id="crystal_ball",
            name="🔮 Bola de Cristal",
            description="Bot 'prevê o futuro' de forma engraçada por 20 minutos",
            cost=600,
            rarity=Rarity.RARE,
            category=ItemCategory.TRANSFORMATION,
            effect="fortune_teller",
            duration_minutes=20,
            usable=True
        ),
        "puzzle_box": ShopItem(
            id="puzzle_box",
            name="🧩 Quebra-Cabeça",
            description="Bot responde com palavras em ordem embaralhada por 15 minutos",
            cost=700,
            rarity=Rarity.RARE,
            category=ItemCategory.TRANSFORMATION,
            effect="scrambled",
            duration_minutes=15,
            usable=True
        ),
        "rose_glasses": ShopItem(
            id="rose_glasses",
            name="🌈 Óculos Coloridos",
            description="Bot vê tudo de forma super positiva e otimista por 25 minutos",
            cost=350,
            rarity=Rarity.COMMON,
            category=ItemCategory.TRANSFORMATION,
            effect="optimistic",
            duration_minutes=25,
            usable=True
        ),
        "dark_glasses": ShopItem(
            id="dark_glasses",
            name="🌑 Óculos Escuros",
            description="Bot vê tudo de forma pessimista e melancólica por 25 minutos",
            cost=350,
            rarity=Rarity.COMMON,
            category=ItemCategory.TRANSFORMATION,
            effect="pessimistic",
            duration_minutes=25,
            usable=True
        ),
        "multiple_personality": ShopItem(
            id="multiple_personality",
            name="🎭 Personalidade Múltipla",
            description="Bot alterna entre 3 personalidades aleatórias por 20 minutos",
            cost=1200,
            rarity=Rarity.EPIC,
            category=ItemCategory.TRANSFORMATION,
            effect="multiple_personality",
            duration_minutes=20,
            usable=True
        ),
        "parrot": ShopItem(
            id="parrot",
            name="🦜 Papagaio",
            description="Bot repete o que você disse de forma engraçada por 15 minutos",
            cost=300,
            rarity=Rarity.COMMON,
            category=ItemCategory.TRANSFORMATION,
            effect="parrot",
            duration_minutes=15,
            usable=True
        ),
        "pirate_wave": ShopItem(
            id="pirate_wave",
            name="🏴‍☠️ Onda do Mar",
            description="Bot responde como um pirata (arr, matey!) por 25 minutos",
            cost=450,
            rarity=Rarity.COMMON,
            category=ItemCategory.TRANSFORMATION,
            effect="pirate",
            duration_minutes=25,
            usable=True
        ),
        
        # Especiais
        "possession_potion": ShopItem(
            id="possession_potion",
            name="🧪 Poção de Possessão",
            description="Bot é possuído por outra persona aleatória por 15 minutos",
            cost=1500,
            rarity=Rarity.EPIC,
            category=ItemCategory.TRANSFORMATION,
            effect="possession",
            duration_minutes=15,
            usable=True
        ),
        "philosopher_stone": ShopItem(
            id="philosopher_stone",
            name="🧿 Pedra Filosofal",
            description="Bot fica filosófico e profundo por 30 minutos",
            cost=800,
            rarity=Rarity.RARE,
            category=ItemCategory.TRANSFORMATION,
            effect="philosopher",
            duration_minutes=30,
            usable=True
        ),
        "grumpy_potion": ShopItem(
            id="grumpy_potion",
            name="😤 Poção Rabugenta",
            description="Bot fica mal-humorado e reclamão por 20 minutos",
            cost=400,
            rarity=Rarity.COMMON,
            category=ItemCategory.TRANSFORMATION,
            effect="grumpy",
            duration_minutes=20,
            usable=True
        ),
        
        # Mini-jogos
        "dart_game": ShopItem(
            id="dart_game",
            name="🎯 Dardo",
            description="Inicia um jogo de 'adivinhe o número' no chat",
            cost=500,
            rarity=Rarity.RARE,
            category=ItemCategory.CONSUMABLE,
            effect="dart_game",
            usable=False
        ),
        "theater_show": ShopItem(
            id="theater_show",
            name="🎭 Teatro",
            description="Bot interpreta uma cena curta com participação dos usuários",
            cost=1800,
            rarity=Rarity.LEGENDARY,
            category=ItemCategory.CONSUMABLE,
            effect="theater",
            usable=False
        ),
    }
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config
        self.db: DatabaseManager = bot.db
        self.permission = PermissionChecker(self.config)
        
        # Itens atualmente na loja rotativa
        self.current_rotating_items: List[str] = []
        
        # Iniciar tarefa de rotação
        self.shop_rotation.start()
    
    def cog_unload(self):
        self.shop_rotation.cancel()
    
    @tasks.loop(hours=72)  # A cada 3 dias
    async def shop_rotation(self):
        """Rotaciona os itens da loja."""
        await self._rotate_shop_items()
    
    @shop_rotation.before_loop
    async def before_shop_rotation(self):
        await self.bot.wait_until_ready()
    
    async def _rotate_shop_items(self):
        """Seleciona 5 itens aleatórios para a loja."""
        # Garantir pelo menos 1 de cada raridade se possível
        items_by_rarity = {
            Rarity.COMMON: [],
            Rarity.RARE: [],
            Rarity.EPIC: [],
            Rarity.LEGENDARY: []
        }
        
        for item_id, item in self.ROTATING_ITEMS.items():
            items_by_rarity[item.rarity].append(item_id)
        
        selected = []
        
        # 2 Comuns
        if items_by_rarity[Rarity.COMMON]:
            selected.extend(random.sample(
                items_by_rarity[Rarity.COMMON], 
                min(2, len(items_by_rarity[Rarity.COMMON]))
            ))
        
        # 2 Raros
        if items_by_rarity[Rarity.RARE]:
            selected.extend(random.sample(
                items_by_rarity[Rarity.RARE],
                min(2, len(items_by_rarity[Rarity.RARE]))
            ))
        
        # 1 Épico ou Lendário
        epic_legendary = items_by_rarity[Rarity.EPIC] + items_by_rarity[Rarity.LEGENDARY]
        if epic_legendary:
            selected.append(random.choice(epic_legendary))
        
        self.current_rotating_items = selected[:5]
        
        # Salvar no banco
        await self._save_shop_rotation()
        
        logger.info(f"Loja rotacionada! Itens: {self.current_rotating_items}")
    
    async def _save_shop_rotation(self):
        """Salva rotação atual no banco."""
        await self.db._connection.execute(
            """INSERT OR REPLACE INTO bot_settings (key, value, updated_at)
               VALUES (?, ?, ?)""",
            ("shop_rotation", json.dumps({
                "items": self.current_rotating_items,
                "rotated_at": datetime.now().isoformat()
            }), datetime.now())
        )
        await self.db._connection.commit()
    
    async def _load_shop_rotation(self):
        """Carrega rotação do banco."""
        async with self.db._connection.execute(
            "SELECT value FROM bot_settings WHERE key = ?",
            ("shop_rotation",)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                data = json.loads(row["value"])
                self.current_rotating_items = data.get("items", [])
                rotated_at = datetime.fromisoformat(data.get("rotated_at", "2000-01-01"))
                
                # Se passou mais de 3 dias, rotacionar
                if datetime.now() - rotated_at >= timedelta(days=3):
                    await self._rotate_shop_items()
            else:
                # Primeira vez
                await self._rotate_shop_items()
    
    # === Comandos ===
    
    loja_group = app_commands.Group(
        name="loja",
        description="Sistema de loja completo"
    )
    
    @loja_group.command(name="fixos", description="Mostra itens fixos da loja")
    async def shop_fixed(self, interaction: discord.Interaction):
        """Mostra itens fixos."""
        embed = discord.Embed(
            title="🏪 Itens Fixos",
            description="Sempre disponíveis para compra",
            color=discord.Color.gold()
        )
        
        for item_id, item in self.FIXED_ITEMS.items():
            embed.add_field(
                name=f"{item.rarity.emoji} {item.name} - {item.cost}🪙",
                value=f"*{item.description}*",
                inline=False
            )
        
        economy = await self.db.get_economy(interaction.user.id)
        embed.set_footer(text=f"Seu saldo: {economy['tokens']}🪙")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @loja_group.command(name="especiais", description="Mostra itens especiais da loja (rotativos)")
    async def shop_special(self, interaction: discord.Interaction):
        """Mostra itens rotativos."""
        # Carregar se necessário
        if not self.current_rotating_items:
            await self._load_shop_rotation()
        
        embed = discord.Embed(
            title="✨ Itens Especiais",
            description="Mudam a cada 3 dias! Compre enquanto durarem!",
            color=discord.Color.purple()
        )
        
        for item_id in self.current_rotating_items:
            if item_id in self.ROTATING_ITEMS:
                item = self.ROTATING_ITEMS[item_id]
                embed.add_field(
                    name=f"{item.rarity.emoji} {item.name} - {item.cost}🪙",
                    value=f"*{item.description}*\n*Duração: {item.duration_minutes} min*" if item.duration_minutes else f"*{item.description}*",
                    inline=False
                )
        
        # Tempo até próxima rotação
        next_rotation = self.shop_rotation.next_iteration
        if next_rotation:
            time_left = next_rotation - datetime.now()
            hours_left = int(time_left.total_seconds() / 3600)
            embed.set_footer(text=f"Próxima rotação em: ~{hours_left}h | Seu saldo: {(await self.db.get_economy(interaction.user.id))['tokens']}🪙")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @loja_group.command(name="comprar", description="Compra um item da loja")
    @app_commands.describe(item="ID do item a comprar")
    async def shop_buy(
        self,
        interaction: discord.Interaction,
        item: str
    ):
        """Compra um item."""
        # Verificar se item existe
        shop_item = None
        
        if item in self.FIXED_ITEMS:
            shop_item = self.FIXED_ITEMS[item]
        elif item in self.ROTATING_ITEMS and item in self.current_rotating_items:
            shop_item = self.ROTATING_ITEMS[item]
        
        if not shop_item:
            await interaction.response.send_message(
                "❌ Item não encontrado ou não está disponível na loja atual.",
                ephemeral=True
            )
            return
        
        # Verificar saldo
        economy = await self.db.get_economy(interaction.user.id)
        
        if economy["tokens"] < shop_item.cost:
            await interaction.response.send_message(
                f"❌ Saldo insuficiente!\n"
                f"Custo: {shop_item.cost}🪙\n"
                f"Seu saldo: {economy['tokens']}🪙",
                ephemeral=True
            )
            return
        
        # Processar compra
        if shop_item.usable:
            # Vai para o inventário
            success = await self._add_to_inventory(
                interaction.user.id, shop_item
            )
        else:
            # Efeito imediato
            success = await self._apply_consumable(
                interaction, shop_item
            )
        
        if success:
            # Remover tokens
            await self.db.remove_tokens(interaction.user.id, shop_item.cost)
            
            # Registrar transação
            await self.db._connection.execute(
                """INSERT INTO shop_transactions 
                   (user_id, item_id, item_name, cost, effect_type, effect_value, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    interaction.user.id,
                    shop_item.id,
                    shop_item.name,
                    shop_item.cost,
                    shop_item.effect,
                    json.dumps(shop_item.to_dict()),
                    datetime.now()
                )
            )
            await self.db._connection.commit()
            
            embed = discord.Embed(
                title="✅ Compra Realizada!",
                description=f"Você comprou **{shop_item.name}**!",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Custo",
                value=f"{shop_item.cost}🪙",
                inline=True
            )
            
            new_balance = economy["tokens"] - shop_item.cost
            embed.add_field(
                name="Novo Saldo",
                value=f"{new_balance}🪙",
                inline=True
            )
            
            if shop_item.usable:
                embed.add_field(
                    name="📦 Inventário",
                    value="Item adicionado ao seu inventário!\nUse `/inventario` para ver.",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                "❌ Erro ao processar compra.",
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
        
        # Calcular recompensa base
        base_reward = 20
        
        # Verificar amuleto da sorte
        has_lucky_charm = await self._check_active_effect(
            interaction.user.id, "lucky_charm"
        )
        
        if has_lucky_charm:
            base_reward = int(base_reward * 1.5)  # +50%
        
        # Chance de item raro na daily
        bonus_item = None
        roll = random.random()
        
        if roll < Rarity.LEGENDARY.chance:
            bonus_item = "Lendário"
            base_reward += 100
        elif roll < Rarity.EPIC.chance + Rarity.LEGENDARY.chance:
            bonus_item = "Épico"
            base_reward += 50
        elif roll < Rarity.RARE.chance + Rarity.EPIC.chance + Rarity.LEGENDARY.chance:
            bonus_item = "Raro"
            base_reward += 25
        
        # Dar recompensa
        await self.db.add_tokens(interaction.user.id, base_reward)
        
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
                str(base_reward),
                datetime.now()
            )
        )
        await self.db._connection.commit()
        
        economy = await self.db.get_economy(interaction.user.id)
        
        embed = discord.Embed(
            title="🎁 Recompensa Diária!",
            description=f"Você recebeu **{base_reward}**🪙!",
            color=discord.Color.green()
        )
        
        if bonus_item:
            embed.add_field(
                name="✨ Bônus de Raridade!",
                value=f"Você teve sorte {bonus_item}! +{base_reward - 20}🪙 extra!",
                inline=False
            )
        
        if has_lucky_charm:
            embed.add_field(
                name="🍀 Amuleto da Sorte",
                value="+50% de bônus aplicado!",
                inline=False
            )
        
        embed.add_field(
            name="Saldo Atual",
            value=f"{economy['tokens']}🪙",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # === Inventário ===
    
    @app_commands.command(name="inventario", description="Mostra seu inventário de itens")
    async def show_inventory(self, interaction: discord.Interaction):
        """Mostra inventário do usuário."""
        inventory = await self._get_inventory(interaction.user.id)
        
        if not inventory:
            await interaction.response.send_message(
                "📭 Seu inventário está vazio.\n"
                "Compre itens na loja com `/loja`!",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title=f"🎒 Inventário de {interaction.user.display_name}",
            description=f"Você tem **{len(inventory)}** item(s)",
            color=discord.Color.blue()
        )
        
        for item_data in inventory:
            item_id = item_data["item_id"]
            
            # Buscar info do item
            if item_id in self.FIXED_ITEMS:
                item_info = self.FIXED_ITEMS[item_id]
            elif item_id in self.ROTATING_ITEMS:
                item_info = self.ROTATING_ITEMS[item_id]
            else:
                continue
            
            quantity = item_data.get("quantity", 1)
            quantity_text = f" (x{quantity})" if quantity > 1 else ""
            
            embed.add_field(
                name=f"{item_info.rarity.emoji} {item_info.name}{quantity_text}",
                value=f"*{item_info.description}*\n"
                      f"Use `/usar {item_id}` para ativar",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="usar", description="Usa um item do seu inventário")
    @app_commands.describe(item="ID do item a usar")
    async def use_item(self, interaction: discord.Interaction, item: str):
        """Usa um item do inventário."""
        # Verificar se tem o item
        has_item = await self._check_inventory(interaction.user.id, item)
        
        if not has_item:
            await interaction.response.send_message(
                "❌ Você não tem este item no inventário.",
                ephemeral=True
            )
            return
        
        # Buscar info do item
        if item in self.FIXED_ITEMS:
            item_info = self.FIXED_ITEMS[item]
        elif item in self.ROTATING_ITEMS:
            item_info = self.ROTATING_ITEMS[item]
        else:
            await interaction.response.send_message(
                "❌ Item não encontrado.",
                ephemeral=True
            )
            return
        
        # Verificar se é usável
        if not item_info.usable:
            await interaction.response.send_message(
                "❌ Este item não pode ser usado desta forma.",
                ephemeral=True
            )
            return
        
        # Aplicar efeito
        success = await self._apply_transformation_effect(
            interaction, item_info
        )
        
        if success:
            # Remover do inventário
            await self._remove_from_inventory(interaction.user.id, item)
            
            await interaction.response.send_message(
                f"✅ **{item_info.name}** ativado!\n"
                f"Duração: {item_info.duration_minutes} minutos",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Erro ao ativar item.",
                ephemeral=True
            )
    
    # === Métodos Auxiliares ===
    
    async def _add_to_inventory(self, user_id: int, item: ShopItem) -> bool:
        """Adiciona item ao inventário."""
        try:
            # Verificar se já tem e é empilhável
            if item.stackable:
                async with self.db._connection.execute(
                    """SELECT quantity FROM user_inventory 
                       WHERE user_id = ? AND item_id = ?""",
                    (user_id, item.id)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row and row["quantity"] < item.max_stack:
                        await self.db._connection.execute(
                            """UPDATE user_inventory 
                               SET quantity = quantity + 1
                               WHERE user_id = ? AND item_id = ?""",
                            (user_id, item.id)
                        )
                        await self.db._connection.commit()
                        return True
            
            # Adicionar novo
            await self.db._connection.execute(
                """INSERT INTO user_inventory 
                   (user_id, item_id, item_data, quantity, acquired_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, item.id, json.dumps(item.to_dict()), 1, datetime.now())
            )
            await self.db._connection.commit()
            return True
        
        except Exception as e:
            logger.error(f"Erro ao adicionar ao inventário: {e}")
            return False
    
    async def _remove_from_inventory(self, user_id: int, item_id: str) -> bool:
        """Remove item do inventário."""
        try:
            async with self.db._connection.execute(
                """SELECT quantity FROM user_inventory 
                   WHERE user_id = ? AND item_id = ?""",
                (user_id, item_id)
            ) as cursor:
                row = await cursor.fetchone()
                
                if not row:
                    return False
                
                if row["quantity"] > 1:
                    await self.db._connection.execute(
                        """UPDATE user_inventory 
                           SET quantity = quantity - 1
                           WHERE user_id = ? AND item_id = ?""",
                        (user_id, item_id)
                    )
                else:
                    await self.db._connection.execute(
                        """DELETE FROM user_inventory 
                           WHERE user_id = ? AND item_id = ?""",
                        (user_id, item_id)
                    )
                
                await self.db._connection.commit()
                return True
        
        except Exception as e:
            logger.error(f"Erro ao remover do inventário: {e}")
            return False
    
    async def _get_inventory(self, user_id: int) -> List[Dict]:
        """Obtém inventário do usuário."""
        async with self.db._connection.execute(
            """SELECT * FROM user_inventory 
               WHERE user_id = ?
               ORDER BY acquired_at DESC""",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def _check_inventory(self, user_id: int, item_id: str) -> bool:
        """Verifica se usuário tem item no inventário."""
        async with self.db._connection.execute(
            """SELECT 1 FROM user_inventory 
               WHERE user_id = ? AND item_id = ?""",
            (user_id, item_id)
        ) as cursor:
            return await cursor.fetchone() is not None
    
    async def _check_active_effect(self, user_id: int, effect_type: str) -> bool:
        """Verifica se usuário tem efeito ativo."""
        async with self.db._connection.execute(
            """SELECT 1 FROM active_effects 
               WHERE user_id = ? AND effect_type = ? AND expires_at > ?""",
            (user_id, effect_type, datetime.now())
        ) as cursor:
            return await cursor.fetchone() is not None
    
    async def _apply_consumable(self, interaction: discord.Interaction, item: ShopItem) -> bool:
        """Aplica item consumível."""
        try:
            if item.effect == "add_image_quota":
                economy = await self.db.get_economy(interaction.user.id)
                new_quota = economy.get("image_quota", 5) + item.effect_value
                await self.db.update_economy(interaction.user.id, image_quota=new_quota)
                return True
            
            elif item.effect == "memory_boost":
                await self.db.add_active_effect(
                    interaction.user.id,
                    interaction.channel_id,
                    "memory_boost",
                    {"multiplier": 2},
                    item.duration_minutes
                )
                return True
            
            elif item.effect == "lucky_charm":
                await self.db.add_active_effect(
                    interaction.user.id,
                    interaction.channel_id,
                    "lucky_charm",
                    {"bonus": 1.5},
                    item.duration_minutes
                )
                return True
            
            # Outros efeitos...
            return True
        
        except Exception as e:
            logger.error(f"Erro ao aplicar consumível: {e}")
            return False
    
    async def _apply_transformation_effect(
        self, 
        interaction: discord.Interaction, 
        item: ShopItem
    ) -> bool:
        """Aplica efeito de transformação no bot."""
        try:
            # Registrar efeito ativo no canal
            await self.db.add_active_effect(
                interaction.user.id,
                interaction.channel_id,
                item.effect,
                {
                    "item_id": item.id,
                    "item_name": item.name,
                    "duration": item.duration_minutes
                },
                item.duration_minutes
            )
            
            # Notificar no canal
            notifications = {
                "old_man": "🦯 **BENGALA ATIVADA!**\n\n'No meu tempo as coisas eram diferentes...' 👴",
                "clown": "🎭 **MASCARA DO PALHAÇO!**\n\n*O bot está no modo engraçado!* 🤡",
                "nerd": "🤓 **ÓCULOS DE NERD!**\n\n'Did you know...?' 🧠",
                "fortune_teller": "🔮 **BOLA DE CRISTAL!**\n\n'Vejo... vejo... algo incrível no seu futuro!' ✨",
                "scrambled": "🧩 **QUEBRA-CABEÇA!**\n\nPalavras... ordem... embaralhadas!",
                "optimistic": "🌈 **ÓCULOS COLORIDOS!**\n\nTudo é maravilhoso! 🌟",
                "pessimistic": "🌑 **ÓCULOS ESCUROS!**\n\n*Suspira* Nada dá certo... 😔",
                "multiple_personality": "🎭 **PERSONALIDADE MÚLTIPLA!**\n\n'Quem sou eu hoje?' 🤔",
                "parrot": "🦜 **PAPAGAIO!**\n\n'Polly wants a cracker!' 🦜",
                "pirate": "🏴‍☠️ **ONDA DO MAR!**\n\n'Arr, matey! Bem-vindo ao meu navio!' ⚓",
                "possession": "🧪 **POSSESSÃO!**\n\n*O bot estremece*\n'Quem... quem sou eu?' 👻",
                "philosopher": "🧿 **PEDRA FILOSOFAL!**\n\n'A vida... o universo... tudo...' 🤔",
                "grumpy": "😤 **POÇÃO RABUGENTA!**\n\n'Humpf! Tudo me irrita!' 😠"
            }
            
            notification = notifications.get(
                item.effect, 
                f"✨ **{item.name} ATIVADO!**"
            )
            
            await interaction.channel.send(notification)
            
            return True
        
        except Exception as e:
            logger.error(f"Erro ao aplicar transformação: {e}")
            return False


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(ShopV2(bot))
