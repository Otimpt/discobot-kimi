"""
Comandos de Chat
Gerencia conversas, modo assistant, e processamento de mensagens
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import discord
from discord import app_commands
from discord.ext import commands, tasks

from core.config import Config
from database.manager import DatabaseManager
from providers.manager import ProviderManager
from utils.permission_checker import PermissionChecker, permission_denied_message
from utils.message_processor import MessageProcessor

logger = logging.getLogger("discord-bot")


class ChatCommands(commands.Cog):
    """Comandos relacionados a chat e conversação."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config: Config = bot.config
        self.db: DatabaseManager = bot.db
        self.provider: ProviderManager = bot.provider
        self.permission = PermissionChecker(self.config)
        self.processor = MessageProcessor(self.config, self.db, self.provider)
        
        # Iniciar tarefa de lembretes
        self.reminder_task.start()
    
    def cog_unload(self):
        """Cleanup quando o cog é descarregado."""
        self.reminder_task.cancel()
    
    @tasks.loop(seconds=30)
    async def reminder_task(self):
        """Verifica e envia lembretes pendentes."""
        try:
            reminders = await self.db.get_pending_reminders()
            for reminder in reminders:
                try:
                    channel = self.bot.get_channel(reminder["channel_id"])
                    if channel:
                        user = self.bot.get_user(reminder["user_id"])
                        embed = discord.Embed(
                            title="⏰ Lembrete",
                            description=reminder["message"],
                            color=discord.Color.blue(),
                            timestamp=datetime.now()
                        )
                        if user:
                            embed.set_footer(text=f"Para: {user.display_name}")
                            await channel.send(content=f"{user.mention}", embed=embed)
                        else:
                            await channel.send(embed=embed)
                    
                    await self.db.complete_reminder(reminder["id"])
                except Exception as e:
                    logger.error(f"Erro ao enviar lembrete {reminder['id']}: {e}")
        except Exception as e:
            logger.error(f"Erro na tarefa de lembretes: {e}")
    
    @reminder_task.before_loop
    async def before_reminder(self):
        await self.bot.wait_until_ready()
    
    # === Comandos Slash ===
    
    @app_commands.command(name="chat", description="Inicia uma conversa com o bot")
    @app_commands.describe(
        mensagem="Sua mensagem para o bot",
        modelo="Modelo a ser usado (opcional)"
    )
    async def chat_command(
        self,
        interaction: discord.Interaction,
        mensagem: str,
        modelo: Optional[str] = None
    ):
        """Comando direto de chat."""
        if not self.permission.check_permissions(interaction):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            response = await self.processor.process_message(
                content=mensagem,
                user=interaction.user,
                channel=interaction.channel,
                guild=interaction.guild,
                model_override=modelo
            )
            
            # Enviar resposta
            chunks = self._split_message(response["content"])
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await interaction.followup.send(chunk)
                else:
                    await interaction.channel.send(chunk)
        
        except Exception as e:
            logger.error(f"Erro no comando chat: {e}")
            await interaction.followup.send(
                f"❌ Erro ao processar mensagem: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="limpar", description="Limpa o histórico de conversa do canal")
    async def clear_command(self, interaction: discord.Interaction):
        """Limpa histórico de conversa."""
        if not self.permission.check_permissions(interaction):
            await interaction.response.send_message(
                permission_denied_message(str(interaction.locale)),
                ephemeral=True
            )
            return
        
        await self.db.clear_conversation(interaction.channel_id)
        
        embed = discord.Embed(
            title="🗑️ Histórico Limpo",
            description="O histórico de conversa deste canal foi apagado.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="historico", description="Mostra estatísticas de uso")
    async def stats_command(self, interaction: discord.Interaction):
        """Mostra estatísticas do usuário."""
        stats = await self.db.get_user_stats(interaction.user.id)
        
        embed = discord.Embed(
            title="📊 Suas Estatísticas (Últimos 30 dias)",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="💬 Mensagens",
            value=str(stats["total_messages"]),
            inline=True
        )
        embed.add_field(
            name="📝 Tokens de Entrada",
            value=f"{stats['total_input_tokens']:,}",
            inline=True
        )
        embed.add_field(
            name="📝 Tokens de Saída",
            value=f"{stats['total_output_tokens']:,}",
            inline=True
        )
        embed.add_field(
            name="🖼️ Imagens Geradas",
            value=str(stats["total_images"]),
            inline=True
        )
        embed.add_field(
            name="📅 Dias Ativos",
            value=str(stats["active_days"]),
            inline=True
        )
        
        embed.set_footer(text=f"Usuário: {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="lembrar", description="Define um lembrete")
    @app_commands.describe(
        tempo="Tempo até o lembrete (ex: 10m, 1h, 30min)",
        mensagem="O que você quer ser lembrado"
    )
    async def remind_command(
        self,
        interaction: discord.Interaction,
        tempo: str,
        mensagem: str
    ):
        """Define um lembrete."""
        # Parse tempo
        try:
            remind_at = self._parse_time(tempo)
        except ValueError as e:
            await interaction.response.send_message(
                f"❌ Formato de tempo inválido. Use: 10m, 1h, 30min, 2d",
                ephemeral=True
            )
            return
        
        reminder_id = await self.db.add_reminder(
            user_id=interaction.user.id,
            channel_id=interaction.channel_id,
            guild_id=interaction.guild_id,
            message=mensagem,
            remind_at=remind_at
        )
        
        time_str = remind_at.strftime("%H:%M")
        date_str = remind_at.strftime("%d/%m/%Y") if remind_at.date() != datetime.now().date() else "hoje"
        
        embed = discord.Embed(
            title="⏰ Lembrete Definido",
            description=f"Vou te lembrar **{date_str}** às **{time_str}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Mensagem", value=mensagem, inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="lembretes", description="Lista seus lembretes ativos")
    async def list_reminders_command(self, interaction: discord.Interaction):
        """Lista lembretes do usuário."""
        reminders = await self.db.get_user_reminders(interaction.user.id)
        
        if not reminders:
            await interaction.response.send_message(
                "📭 Você não tem lembretes ativos.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="📋 Seus Lembretes",
            color=discord.Color.blue()
        )
        
        for reminder in reminders:
            remind_at = datetime.fromisoformat(reminder["remind_at"]) if isinstance(reminder["remind_at"], str) else reminder["remind_at"]
            time_str = remind_at.strftime("%d/%m %H:%M")
            embed.add_field(
                name=f"ID: {reminder['id']} - {time_str}",
                value=reminder["message"][:100] + "..." if len(reminder["message"]) > 100 else reminder["message"],
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="cancelar_lembrete", description="Cancela um lembrete")
    @app_commands.describe(lembrete_id="ID do lembrete a cancelar")
    async def cancel_reminder_command(
        self,
        interaction: discord.Interaction,
        lembrete_id: int
    ):
        """Cancela um lembrete."""
        # Verificar se o lembrete pertence ao usuário
        reminders = await self.db.get_user_reminders(interaction.user.id)
        if not any(r["id"] == lembrete_id for r in reminders):
            await interaction.response.send_message(
                "❌ Lembrete não encontrado ou não pertence a você.",
                ephemeral=True
            )
            return
        
        await self.db.delete_reminder(lembrete_id)
        
        await interaction.response.send_message(
            "✅ Lembrete cancelado com sucesso!",
            ephemeral=True
        )
    
    # === Eventos ===
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Processa mensagens recebidas."""
        if message.author.bot:
            return
        
        # Verificar se é DM
        is_dm = isinstance(message.channel, discord.DMChannel)
        
        if not is_dm:
            # Verificar configurações do canal
            settings = await self.db.get_channel_settings(message.channel.id)
            
            if not settings.get("is_active", False):
                return
            
            # Verificar permissões
            if not self.permission.check_permissions(message):
                return
        
        # Verificar gatilhos
        should_respond = await self._check_triggers(message, settings if not is_dm else {})
        
        if not should_respond:
            return
        
        # Processar mensagem
        async with message.channel.typing():
            try:
                response = await self.processor.process_message(
                    content=message.content,
                    user=message.author,
                    channel=message.channel,
                    guild=message.guild,
                    referenced_message=message.reference.resolved if message.reference else None
                )
                
                # Enviar resposta
                chunks = self._split_message(response["content"])
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        await message.reply(chunk, mention_author=False)
                    else:
                        await message.channel.send(chunk)
                
                # Registrar uso
                await self.db.record_usage(
                    user_id=message.author.id,
                    guild_id=message.guild.id if message.guild else None,
                    model=response.get("model", "unknown"),
                    tokens_input=response.get("usage", {}).get("input_tokens", 0),
                    tokens_output=response.get("usage", {}).get("output_tokens", 0)
                )
                
            except Exception as e:
                logger.error(f"Erro ao processar mensagem: {e}")
                await message.reply(
                    f"❌ Desculpe, ocorreu um erro ao processar sua mensagem.",
                    mention_author=False
                )
    
    async def _check_triggers(
        self,
        message: discord.Message,
        settings: Dict[str, Any]
    ) -> bool:
        """
        Verifica se deve responder à mensagem baseado nos gatilhos.
        
        REGRAS:
        1. Reply SEMPRE funciona (não é configurável) - responde em reply às mensagens do bot
        2. Modo chatbot - responde sem gatilhos (IA decide)
        3. Modo interativo - modo próprio de chatbot inteligente (não pode ser mudado)
        4. Outros gatilhos são configuráveis
        """
        # ============================================
        # 1. REPLY SEMPRE FUNCIONA (não configurável)
        # ============================================
        is_reply = message.reference is not None and message.reference.resolved
        if is_reply and hasattr(message.reference.resolved, 'author'):
            is_reply_to_bot = message.reference.resolved.author.id == self.bot.user.id
            if is_reply_to_bot:
                return True  # Sempre responde em reply às mensagens do bot
        
        # ============================================
        # 2. VERIFICAR MODO DE OPERAÇÃO
        # ============================================
        mode = settings.get("mode", "normal")
        
        # Modo Chatbot - responde sem gatilhos (IA decide)
        if mode == "chatbot":
            return await self._should_interject_chatbot(message, settings)
        
        # Modo Interativo - modo próprio de chatbot inteligente
        if mode == "interactive":
            return await self._should_interject_interactive(message, settings)
        
        # ============================================
        # 3. GATILHOS CONFIGURÁVEIS (para modos normal/assistant/roleplay)
        # ============================================
        
        # Gatilho: Menção (@Bot)
        trigger_on_mention = settings.get("trigger_on_mention", True)
        is_mentioned = self.bot.user in message.mentions
        
        # Gatilho: Prefixo configurável (padrão: !)
        trigger_on_prefix = settings.get("trigger_on_prefix", False)
        prefix = settings.get("trigger_prefix", "!")
        has_prefix = message.content.startswith(prefix)
        
        # Gatilho: Interrogação (?) = ambos (! + @bot)
        trigger_on_question = settings.get("trigger_on_question", False)
        starts_with_question = message.content.startswith("?")
        
        # Gatilho: Ambos (prefixo OU menção)
        trigger_on_both = settings.get("trigger_on_both", False)
        
        # Verificar gatilhos ativos
        if trigger_on_mention and is_mentioned:
            return True
        
        if trigger_on_prefix and has_prefix:
            return True
        
        if trigger_on_question and starts_with_question:
            # "?" = ambos (! + @bot) - ativa tanto prefixo quanto menção
            return True
        
        if trigger_on_both and (has_prefix or is_mentioned):
            return True
        
        return False
    
    async def _should_interject_chatbot(
        self,
        message: discord.Message,
        settings: Dict[str, Any]
    ) -> bool:
        """
        Modo Chatbot: Decide quando responder sem gatilhos.
        A IA decide baseado no contexto da conversa.
        """
        sensitivity = settings.get("trigger_chatbot_sensitivity", "normal")
        
        # Configurações de sensibilidade
        sensitivity_config = {
            "low": {"min_messages": 10, "response_chance": 0.1},
            "normal": {"min_messages": 5, "response_chance": 0.3},
            "high": {"min_messages": 2, "response_chance": 0.6}
        }
        
        config = sensitivity_config.get(sensitivity, sensitivity_config["normal"])
        
        # Pegar histórico recente
        history = await self.db.get_conversation_history(
            message.channel.id,
            limit=config["min_messages"]
        )
        
        # Se poucas mensagens, não responde
        if len(history) < config["min_messages"]:
            return False
        
        # Verificar se foi mencionado indiretamente
        content_lower = message.content.lower()
        indirect_mentions = ["bot", "ia", "inteligência", "você", "vc"]
        if any(word in content_lower for word in indirect_mentions):
            return True
        
        # Verificar se é pergunta
        if "?" in message.content:
            return True
        
        # Chance aleatória baseada na sensibilidade
        import random
        return random.random() < config["response_chance"]
    
    async def _should_interject_interactive(
        self,
        message: discord.Message,
        settings: Dict[str, Any]
    ) -> bool:
        """
        Modo Interativo: Membro do servidor com personalidade complexa.
        Este modo é mais sofisticado - a persona decide quando responder.
        """
        # Pegar persona evolutiva ativa
        persona_id = settings.get("persona_id")
        if not persona_id:
            # Se não tem persona, usa lógica do chatbot
            return await self._should_interject_chatbot(message, settings)
        
        # Buscar persona evolutiva
        # (implementar na database)
        
        # Verificar relacionamento com o usuário
        # Se conhece bem o usuário, mais propenso a responder
        
        # Verificar contexto emocional
        # Se a conversa está animada, participar
        
        # Verificar se foi mencionado direta ou indiretamente
        is_mentioned = self.bot.user in message.mentions
        content_lower = message.content.lower()
        
        # Palavras que indicam que estão falando com/falam do bot
        bot_references = [
            self.bot.user.name.lower(),
            self.bot.user.display_name.lower(),
            "bot", "ia", "inteligência artificial",
            "você", "vc", "tu", "cê"
        ]
        
        referenced = any(ref in content_lower for ref in bot_references)
        
        # Se mencionado diretamente, sempre responde
        if is_mentioned:
            return True
        
        # Se referenciado indiretamente, alta chance
        if referenced:
            import random
            return random.random() < 0.7
        
        # Pegar histórico para contexto
        history = await self.db.get_conversation_history(
            message.channel.id,
            limit=10
        )
        
        # Se o bot participou recentemente, continuar participando
        recent_bot_messages = [
            h for h in history[-3:] 
            if h.get("role") == "assistant" or h.get("user_id") == 0
        ]
        
        if len(recent_bot_messages) >= 2:
            import random
            return random.random() < 0.5
        
        # Chance base de participar (baixa para não ser invasivo)
        import random
        return random.random() < 0.15
    
    async def _should_interject(
        self,
        message: discord.Message,
        settings: Dict[str, Any]
    ) -> bool:
        """Decide se o bot deve intervir na conversa (modo inteligente)."""
        chatbot_mode = settings.get("chatbot_mode", 1)
        
        # Modo frenético - sempre responde
        if chatbot_mode == 4:
            return True
        
        # Modos inteligente, fluido, roleplay
        if chatbot_mode in [1, 3, 5]:
            # Pegar histórico recente
            history = await self.db.get_conversation_history(
                message.channel.id,
                limit=5
            )
            
            messages = []
            for h in history:
                role = "assistant" if h["role"] == "assistant" else "user"
                messages.append({
                    "role": role,
                    "content": h["content"][:200]
                })
            
            # Adicionar mensagem atual
            messages.append({
                "role": "user",
                "content": message.content[:200]
            })
            
            # Usar modelo leve para decidir
            try:
                sensitivity = "high" if chatbot_mode == 3 else "normal"
                prompt = f"Should an AI assistant respond to this conversation? Reply ONLY 'YES' or 'NO'. Context: {messages}"
                
                response = await self.provider.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    model="gpt-4o-mini",
                    temperature=0.0,
                    max_tokens=5
                )
                
                return "YES" in response["content"].upper()
            except:
                # Em caso de erro, não intervém
                return False
        
        return False
    
    def _split_message(self, content: str, max_length: int = 2000) -> List[str]:
        """Divide mensagem longa em chunks."""
        if len(content) <= max_length:
            return [content]
        
        chunks = []
        current = ""
        
        for line in content.split("\n"):
            if len(current) + len(line) + 1 > max_length:
                if current:
                    chunks.append(current)
                current = line
            else:
                current += "\n" + line if current else line
        
        if current:
            chunks.append(current)
        
        return chunks
    
    def _parse_time(self, time_str: str) -> datetime:
        """Parse string de tempo para datetime."""
        time_str = time_str.lower().strip()
        
        # Extrair número e unidade
        import re
        match = re.match(r'(\d+)\s*(m|min|mins|minuto|minutos|h|hr|hrs|hora|horas|d|dia|dias)', time_str)
        
        if not match:
            raise ValueError("Formato inválido")
        
        amount = int(match.group(1))
        unit = match.group(2)
        
        if unit in ['m', 'min', 'mins', 'minuto', 'minutos']:
            delta = timedelta(minutes=amount)
        elif unit in ['h', 'hr', 'hrs', 'hora', 'horas']:
            delta = timedelta(hours=amount)
        elif unit in ['d', 'dia', 'dias']:
            delta = timedelta(days=amount)
        else:
            raise ValueError("Unidade inválida")
        
        return datetime.now() + delta


async def setup(bot: commands.Bot):
    """Setup do cog."""
    await bot.add_cog(ChatCommands(bot))
