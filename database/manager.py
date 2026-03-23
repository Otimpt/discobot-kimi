"""
Gerenciador de Banco de Dados
SQLite com suporte a async e todas as tabelas necessárias
"""

import aiosqlite
import json
import shutil
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import logging

logger = logging.getLogger("discord-bot")


class DatabaseManager:
    """Gerencia todas as operações de banco de dados."""
    
    def __init__(self, db_path: str = "data/bot_database.db"):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
        
    async def initialize(self):
        """Inicializa o banco de dados e cria tabelas."""
        # Criar diretório se não existir
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        
        await self._create_tables()
        logger.info(f"📊 Banco de dados inicializado: {self.db_path}")
    
    async def _create_tables(self):
        """Cria todas as tabelas necessárias."""
        
        # Configurações por canal (NOVO SISTEMA DE GATILHOS)
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS channel_settings (
                channel_id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                mode TEXT DEFAULT 'smart',
                model TEXT,
                assistant_id TEXT,
                prompt_id TEXT,
                persona_id TEXT,
                system_prompt TEXT,
                
                -- NOVO SISTEMA DE GATILHOS
                trigger_reply_to_bot BOOLEAN DEFAULT 1,      -- Responder em reply às mensagens do bot
                trigger_on_mention BOOLEAN DEFAULT 1,         -- Responder quando mencionado (@Bot)
                trigger_on_prefix BOOLEAN DEFAULT 0,          -- Responder quando usar prefixo (!)
                trigger_prefix TEXT DEFAULT '!',
                trigger_on_question BOOLEAN DEFAULT 0,        -- Responder quando msg começa com ?
                trigger_chatbot_mode BOOLEAN DEFAULT 0,       -- Modo chatbot (sem gatilhos)
                trigger_chatbot_sensitivity TEXT DEFAULT 'normal',  -- low, normal, high
                
                -- Outras configurações
                safety_mode TEXT DEFAULT 'standard',
                use_memory BOOLEAN DEFAULT 1,
                memory_max_messages INTEGER DEFAULT 50,
                memory_context_hours INTEGER DEFAULT 24,
                isolated_context BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Configurações por servidor (CONFIGURAÇÕES PADRÃO DO SERVIDOR)
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                
                -- Configurações padrão do servidor
                default_model TEXT,
                default_persona TEXT,
                default_system_prompt TEXT,
                default_mode TEXT DEFAULT 'smart',
                
                -- Gatilhos padrão
                default_trigger_reply_to_bot BOOLEAN DEFAULT 1,
                default_trigger_on_mention BOOLEAN DEFAULT 1,
                default_trigger_on_prefix BOOLEAN DEFAULT 0,
                default_trigger_prefix TEXT DEFAULT '!',
                default_trigger_on_question BOOLEAN DEFAULT 0,
                default_trigger_chatbot_mode BOOLEAN DEFAULT 0,
                
                -- Outras configurações
                default_safety_mode TEXT DEFAULT 'standard',
                default_use_memory BOOLEAN DEFAULT 1,
                default_image_quota INTEGER DEFAULT 5,
                
                -- Configurações de boas-vindas
                welcome_channel_id INTEGER,
                welcome_enabled BOOLEAN DEFAULT 0,
                welcome_message TEXT,
                welcome_use_ai BOOLEAN DEFAULT 1,
                
                -- Configurações de moderação
                auto_mod_enabled BOOLEAN DEFAULT 0,
                log_channel_id INTEGER,
                mod_role_id INTEGER,
                admin_role_id INTEGER,
                
                -- Permissões do servidor
                blocked_users TEXT,           -- JSON array de user IDs
                blocked_roles TEXT,           -- JSON array de role IDs
                blocked_channels TEXT,        -- JSON array de channel IDs
                allowed_channels TEXT,        -- JSON array (vazio = todos)
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Histórico de conversas
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                guild_id INTEGER,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                model TEXT,
                tokens_used INTEGER DEFAULT 0,
                has_attachments BOOLEAN DEFAULT 0,
                attachment_types TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_channel 
            ON conversations(channel_id, created_at)
        """)
        
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_user 
            ON conversations(user_id, created_at)
        """)
        
        # Memória de fatos (usuários)
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS user_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                fact TEXT,
                importance REAL DEFAULT 1.0,
                is_permanent BOOLEAN DEFAULT 0,
                origin_persona TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_facts_user 
            ON user_facts(user_id)
        """)
        
        # Memória de fatos (servidores)
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS guild_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                fact TEXT,
                importance REAL DEFAULT 1.0,
                is_permanent BOOLEAN DEFAULT 0,
                origin_persona TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Personas
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS personas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                name TEXT,
                system_prompt TEXT,
                prompt_id TEXT,
                description TEXT,
                avatar_url TEXT,
                is_global BOOLEAN DEFAULT 0,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, name)
            )
        """)
        
        # Identidade de personas (evolução)
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS persona_identities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                persona_id TEXT,
                traits TEXT,
                archetype TEXT,
                mood TEXT,
                tastes TEXT,
                beliefs TEXT,
                evolution_summary TEXT,
                last_updated INTEGER
            )
        """)
        
        # Uploads/arquivos
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                file_path TEXT,
                content_type TEXT,
                file_size INTEGER,
                user_id INTEGER,
                channel_id INTEGER,
                guild_id INTEGER,
                is_private BOOLEAN DEFAULT 0,
                embedding_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Economia/Tokens
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS economy (
                user_id INTEGER PRIMARY KEY,
                tokens INTEGER DEFAULT 0,
                image_quota INTEGER DEFAULT 5,
                weekly_image_used INTEGER DEFAULT 0,
                weekly_reset_date TIMESTAMP,
                premium_features TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Efeitos ativos (itens da loja)
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS active_effects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                channel_id INTEGER,
                effect_type TEXT,
                effect_data TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Lembretes
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                channel_id INTEGER,
                guild_id INTEGER,
                message TEXT,
                remind_at TIMESTAMP,
                is_recurring BOOLEAN DEFAULT 0,
                recurrence_pattern TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        
        # Estatísticas
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                guild_id INTEGER,
                model TEXT,
                tokens_input INTEGER DEFAULT 0,
                tokens_output INTEGER DEFAULT 0,
                messages_sent INTEGER DEFAULT 0,
                images_generated INTEGER DEFAULT 0,
                date TEXT,
                UNIQUE(user_id, guild_id, model, date)
            )
        """)
        
        # Vetores (para RAG simples com SQLite)
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS vectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT,
                embedding BLOB,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Banimentos globais (apenas dono pode adicionar)
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS global_bans (
                user_id INTEGER PRIMARY KEY,
                reason TEXT,
                banned_by INTEGER,
                banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
        
        # Configurações do bot (para o dono)
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Descrições de emojis
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS emoji_descriptions (
                emoji_id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Modelos customizados
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS custom_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                provider TEXT,
                model_id TEXT,
                temperature REAL,
                max_tokens INTEGER,
                vision_capable BOOLEAN DEFAULT 0,
                supports_tools BOOLEAN DEFAULT 1,
                extra_params TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Transações da loja
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS shop_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_id TEXT,
                item_name TEXT,
                cost INTEGER,
                effect_type TEXT,
                effect_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Cache LangCache (se habilitado)
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS semantic_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_hash TEXT UNIQUE,
                query TEXT,
                response TEXT,
                embedding BLOB,
                model TEXT,
                hits INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # === NOVAS TABELAS PARA SISTEMA V2 ===
        
        # Inventário de usuários
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS user_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                item_data TEXT,
                quantity INTEGER DEFAULT 1,
                acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, item_id)
            )
        """)
        
        # Sistema de memória hierárquica V2
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                context_id TEXT NOT NULL,           -- guild_id ou user_id (DM)
                tier TEXT NOT NULL,                 -- short_term, medium_term, long_term, permanent
                memory_type TEXT DEFAULT 'conversation',  -- conversation, fact, joke, user_info, etc
                data TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                importance REAL DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                source_guild_id TEXT,               -- Servidor de origem
                source_user_id TEXT,                -- Usuário relacionado
                is_permanent BOOLEAN DEFAULT 0,     -- Nunca apagada
                permanent_reason TEXT,              -- Por que é permanente
                permanent_since TIMESTAMP,          -- Quando virou permanente
                shared_with_guilds TEXT             -- JSON array de guilds que compartilham
            )
        """)
        
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_context 
            ON memories(context_id, tier, timestamp)
        """)
        
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_access 
            ON memories(last_accessed, access_count)
        """)
        
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_user 
            ON memories(source_user_id, tier)
        """)
        
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_cross_server 
            ON memories(source_user_id, source_guild_id, importance)
            WHERE tier IN ('long_term', 'permanent')
        """)
        
        # Configuração de memória por contexto
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS memory_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context_id TEXT NOT NULL,
                tier TEXT NOT NULL,
                provider TEXT NOT NULL,
                connection_string TEXT,
                api_key TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(context_id, tier)
            )
        """)
        
        # Configurações de DM (chat privado)
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS dm_settings (
                user_id INTEGER PRIMARY KEY,
                is_active BOOLEAN DEFAULT 1,
                mode TEXT DEFAULT 'smart',
                model TEXT,
                persona_id TEXT,
                system_prompt TEXT,
                memory_enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self._connection.commit()
    
    async def close(self):
        """Fecha a conexão com o banco de dados."""
        if self._connection:
            await self._connection.close()
            logger.info("📊 Conexão com banco de dados fechada")
    
    # === Channel Settings ===
    
    async def get_channel_settings(self, channel_id: int) -> Dict[str, Any]:
        """Obtém configurações de um canal."""
        async with self._connection.execute(
            "SELECT * FROM channel_settings WHERE channel_id = ?",
            (channel_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return {}
    
    async def set_channel_settings(self, channel_id: int, guild_id: int, **kwargs):
        """Define configurações de um canal."""
        # Verificar se já existe
        existing = await self.get_channel_settings(channel_id)
        
        if existing:
            # Update
            fields = []
            values = []
            for key, value in kwargs.items():
                fields.append(f"{key} = ?")
                values.append(value)
            values.extend([datetime.now(), channel_id])
            
            query = f"UPDATE channel_settings SET {', '.join(fields)}, updated_at = ? WHERE channel_id = ?"
            await self._connection.execute(query, values)
        else:
            # Insert
            fields = ["channel_id", "guild_id"] + list(kwargs.keys())
            values = [channel_id, guild_id] + list(kwargs.values())
            placeholders = ", ".join(["?"] * len(fields))
            
            query = f"INSERT INTO channel_settings ({', '.join(fields)}) VALUES ({placeholders})"
            await self._connection.execute(query, values)
        
        await self._connection.commit()
    
    async def set_channel_active(self, channel_id: int, active: bool):
        """Ativa/desativa o bot em um canal."""
        await self._connection.execute(
            "UPDATE channel_settings SET is_active = ?, updated_at = ? WHERE channel_id = ?",
            (active, datetime.now(), channel_id)
        )
        await self._connection.commit()
    
    # === Conversations ===
    
    async def add_message(
        self,
        channel_id: int,
        user_id: int,
        role: str,
        content: str,
        guild_id: Optional[int] = None,
        model: Optional[str] = None,
        tokens_used: int = 0,
        has_attachments: bool = False,
        attachment_types: Optional[List[str]] = None
    ):
        """Adiciona uma mensagem ao histórico."""
        await self._connection.execute(
            """INSERT INTO conversations 
               (channel_id, guild_id, user_id, role, content, model, tokens_used, 
                has_attachments, attachment_types, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                channel_id, guild_id, user_id, role, content, model, tokens_used,
                has_attachments,
                json.dumps(attachment_types) if attachment_types else None,
                datetime.now()
            )
        )
        await self._connection.commit()
    
    async def get_conversation_history(
        self,
        channel_id: int,
        limit: int = 50,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Obtém histórico de conversa de um canal."""
        if since:
            async with self._connection.execute(
                """SELECT * FROM conversations 
                   WHERE channel_id = ? AND created_at > ?
                   ORDER BY created_at DESC LIMIT ?""",
                (channel_id, since, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in reversed(rows)]
        else:
            async with self._connection.execute(
                """SELECT * FROM conversations 
                   WHERE channel_id = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (channel_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in reversed(rows)]
    
    async def clear_conversation(self, channel_id: int):
        """Limpa histórico de conversa de um canal."""
        await self._connection.execute(
            "DELETE FROM conversations WHERE channel_id = ?",
            (channel_id,)
        )
        await self._connection.commit()
    
    # === User Facts ===
    
    async def add_user_fact(
        self,
        user_id: int,
        fact: str,
        importance: float = 1.0,
        is_permanent: bool = False,
        origin_persona: Optional[str] = None
    ):
        """Adiciona um fato sobre um usuário."""
        await self._connection.execute(
            """INSERT INTO user_facts 
               (user_id, fact, importance, is_permanent, origin_persona, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, fact, importance, is_permanent, origin_persona, datetime.now())
        )
        await self._connection.commit()
    
    async def get_user_facts(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtém fatos sobre um usuário."""
        async with self._connection.execute(
            """SELECT * FROM user_facts 
               WHERE user_id = ?
               ORDER BY importance DESC, created_at DESC
               LIMIT ?""",
            (user_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # === Guild Facts ===
    
    async def add_guild_fact(
        self,
        guild_id: int,
        fact: str,
        importance: float = 1.0,
        is_permanent: bool = False,
        origin_persona: Optional[str] = None
    ):
        """Adiciona um fato sobre um servidor."""
        await self._connection.execute(
            """INSERT INTO guild_facts 
               (guild_id, fact, importance, is_permanent, origin_persona, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (guild_id, fact, importance, is_permanent, origin_persona, datetime.now())
        )
        await self._connection.commit()
    
    async def get_guild_facts(
        self,
        guild_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtém fatos sobre um servidor."""
        async with self._connection.execute(
            """SELECT * FROM guild_facts 
               WHERE guild_id = ?
               ORDER BY importance DESC, created_at DESC
               LIMIT ?""",
            (guild_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # === Personas ===
    
    async def create_persona(
        self,
        guild_id: Optional[int],
        name: str,
        system_prompt: str,
        prompt_id: Optional[str] = None,
        description: Optional[str] = None,
        avatar_url: Optional[str] = None,
        is_global: bool = False,
        created_by: Optional[int] = None
    ):
        """Cria uma nova persona."""
        await self._connection.execute(
            """INSERT INTO personas 
               (guild_id, name, system_prompt, prompt_id, description, avatar_url, 
                is_global, created_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(guild_id, name) DO UPDATE SET
               system_prompt = excluded.system_prompt,
               prompt_id = excluded.prompt_id,
               description = excluded.description,
               updated_at = ?""",
            (guild_id, name, system_prompt, prompt_id, description, avatar_url,
             is_global, created_by, datetime.now(), datetime.now())
        )
        await self._connection.commit()
    
    async def get_persona(
        self,
        name: str,
        guild_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Obtém uma persona pelo nome."""
        # Primeiro tentar persona do servidor
        if guild_id:
            async with self._connection.execute(
                "SELECT * FROM personas WHERE name = ? AND guild_id = ?",
                (name, guild_id)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
        
        # Depois tentar persona global
        async with self._connection.execute(
            "SELECT * FROM personas WHERE name = ? AND is_global = 1",
            (name,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
        
        return None
    
    async def list_personas(
        self,
        guild_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Lista todas as personas disponíveis."""
        if guild_id:
            async with self._connection.execute(
                """SELECT * FROM personas 
                   WHERE guild_id = ? OR is_global = 1
                   ORDER BY is_global DESC, name""",
                (guild_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        else:
            async with self._connection.execute(
                "SELECT * FROM personas WHERE is_global = 1 ORDER BY name"
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def delete_persona(self, name: str, guild_id: int):
        """Deleta uma persona."""
        await self._connection.execute(
            "DELETE FROM personas WHERE name = ? AND guild_id = ?",
            (name, guild_id)
        )
        await self._connection.commit()
    
    # === Economy ===
    
    async def get_economy(self, user_id: int) -> Dict[str, Any]:
        """Obtém dados econômicos de um usuário."""
        async with self._connection.execute(
            "SELECT * FROM economy WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            
            # Criar entrada padrão
            await self._connection.execute(
                "INSERT INTO economy (user_id, tokens) VALUES (?, 100)",
                (user_id,)
            )
            await self._connection.commit()
            
            return {
                "user_id": user_id,
                "tokens": 100,
                "image_quota": 5,
                "weekly_image_used": 0
            }
    
    async def update_economy(
        self,
        user_id: int,
        tokens: Optional[int] = None,
        image_quota: Optional[int] = None,
        weekly_image_used: Optional[int] = None
    ):
        """Atualiza dados econômicos de um usuário."""
        fields = []
        values = []
        
        if tokens is not None:
            fields.append("tokens = ?")
            values.append(tokens)
        if image_quota is not None:
            fields.append("image_quota = ?")
            values.append(image_quota)
        if weekly_image_used is not None:
            fields.append("weekly_image_used = ?")
            values.append(weekly_image_used)
        
        if fields:
            values.extend([datetime.now(), user_id])
            query = f"UPDATE economy SET {', '.join(fields)}, updated_at = ? WHERE user_id = ?"
            await self._connection.execute(query, values)
            await self._connection.commit()
    
    async def add_tokens(self, user_id: int, amount: int):
        """Adiciona tokens a um usuário."""
        economy = await self.get_economy(user_id)
        new_balance = economy.get("tokens", 0) + amount
        await self.update_economy(user_id, tokens=new_balance)
    
    async def remove_tokens(self, user_id: int, amount: int) -> bool:
        """Remove tokens de um usuário. Retorna True se sucesso."""
        economy = await self.get_economy(user_id)
        current = economy.get("tokens", 0)
        
        if current >= amount:
            await self.update_economy(user_id, tokens=current - amount)
            return True
        return False
    
    # === Image Quota ===
    
    async def check_and_use_image_quota(self, user_id: int) -> bool:
        """Verifica e usa cota de imagem do usuário. Retorna True se permitido."""
        economy = await self.get_economy(user_id)
        
        # Verificar reset semanal
        weekly_reset = economy.get("weekly_reset_date")
        if weekly_reset:
            reset_date = datetime.fromisoformat(weekly_reset) if isinstance(weekly_reset, str) else weekly_reset
            if datetime.now() - reset_date >= timedelta(days=7):
                # Resetar contador semanal
                await self._connection.execute(
                    """UPDATE economy 
                       SET weekly_image_used = 0, weekly_reset_date = ?
                       WHERE user_id = ?""",
                    (datetime.now(), user_id)
                )
                economy["weekly_image_used"] = 0
        
        weekly_used = economy.get("weekly_image_used", 0)
        quota = economy.get("image_quota", 5)
        
        if weekly_used < quota:
            # Usar cota
            await self._connection.execute(
                "UPDATE economy SET weekly_image_used = weekly_image_used + 1 WHERE user_id = ?",
                (user_id,)
            )
            await self._connection.commit()
            return True
        
        return False
    
    async def get_image_quota_status(self, user_id: int) -> Dict[str, Any]:
        """Obtém status da cota de imagens."""
        economy = await self.get_economy(user_id)
        
        return {
            "weekly_used": economy.get("weekly_image_used", 0),
            "quota": economy.get("image_quota", 5),
            "remaining": economy.get("image_quota", 5) - economy.get("weekly_image_used", 0),
            "resets_in": self._get_time_until_reset(economy.get("weekly_reset_date"))
        }
    
    def _get_time_until_reset(self, reset_date) -> str:
        """Calcula tempo até o reset semanal."""
        if not reset_date:
            return "7 dias"
        
        if isinstance(reset_date, str):
            reset_date = datetime.fromisoformat(reset_date)
        
        next_reset = reset_date + timedelta(days=7)
        time_left = next_reset - datetime.now()
        
        if time_left.total_seconds() <= 0:
            return "Em breve"
        
        days = time_left.days
        hours = time_left.seconds // 3600
        
        if days > 0:
            return f"{days}d {hours}h"
        return f"{hours}h"
    
    # === Uploads ===
    
    async def add_upload(
        self,
        filename: str,
        file_path: str,
        content_type: str,
        file_size: int,
        user_id: int,
        channel_id: int,
        guild_id: Optional[int] = None,
        is_private: bool = False
    ) -> int:
        """Registra um upload."""
        cursor = await self._connection.execute(
            """INSERT INTO uploads 
               (filename, file_path, content_type, file_size, user_id, channel_id, 
                guild_id, is_private, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (filename, file_path, content_type, file_size, user_id, channel_id,
             guild_id, is_private, datetime.now())
        )
        await self._connection.commit()
        return cursor.lastrowid
    
    async def get_uploads(
        self,
        user_id: Optional[int] = None,
        guild_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Lista uploads com filtros opcionais."""
        query = "SELECT * FROM uploads WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        if guild_id:
            query += " AND guild_id = ?"
            params.append(guild_id)
        if search:
            query += " AND filename LIKE ?"
            params.append(f"%{search}%")
        
        query += " ORDER BY created_at DESC"
        
        async with self._connection.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_upload_by_id(self, upload_id: int) -> Optional[Dict[str, Any]]:
        """Obtém um upload pelo ID."""
        async with self._connection.execute(
            "SELECT * FROM uploads WHERE id = ?",
            (upload_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    # === Reminders ===
    
    async def add_reminder(
        self,
        user_id: int,
        channel_id: int,
        message: str,
        remind_at: datetime,
        guild_id: Optional[int] = None,
        is_recurring: bool = False,
        recurrence_pattern: Optional[str] = None
    ) -> int:
        """Adiciona um lembrete."""
        cursor = await self._connection.execute(
            """INSERT INTO reminders 
               (user_id, channel_id, guild_id, message, remind_at, is_recurring, 
                recurrence_pattern, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, channel_id, guild_id, message, remind_at, is_recurring,
             recurrence_pattern, datetime.now())
        )
        await self._connection.commit()
        return cursor.lastrowid
    
    async def get_pending_reminders(self) -> List[Dict[str, Any]]:
        """Obtém lembretes pendentes."""
        async with self._connection.execute(
            """SELECT * FROM reminders 
               WHERE remind_at <= ? AND completed_at IS NULL
               ORDER BY remind_at""",
            (datetime.now(),)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def complete_reminder(self, reminder_id: int):
        """Marca um lembrete como completo."""
        await self._connection.execute(
            "UPDATE reminders SET completed_at = ? WHERE id = ?",
            (datetime.now(), reminder_id)
        )
        await self._connection.commit()
    
    async def delete_reminder(self, reminder_id: int):
        """Deleta um lembrete."""
        await self._connection.execute(
            "DELETE FROM reminders WHERE id = ?",
            (reminder_id,)
        )
        await self._connection.commit()
    
    async def get_user_reminders(self, user_id: int) -> List[Dict[str, Any]]:
        """Obtém lembretes de um usuário."""
        async with self._connection.execute(
            """SELECT * FROM reminders 
               WHERE user_id = ? AND completed_at IS NULL
               ORDER BY remind_at""",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # === Custom Models ===
    
    async def add_custom_model(
        self,
        name: str,
        provider: str,
        model_id: str,
        temperature: float = 0.9,
        max_tokens: int = 4096,
        vision_capable: bool = False,
        supports_tools: bool = True,
        extra_params: Optional[Dict] = None,
        created_by: Optional[int] = None
    ):
        """Adiciona um modelo customizado."""
        await self._connection.execute(
            """INSERT INTO custom_models 
               (name, provider, model_id, temperature, max_tokens, vision_capable,
                supports_tools, extra_params, created_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(name) DO UPDATE SET
               provider = excluded.provider,
               model_id = excluded.model_id,
               temperature = excluded.temperature,
               max_tokens = excluded.max_tokens,
               vision_capable = excluded.vision_capable,
               supports_tools = excluded.supports_tools,
               extra_params = excluded.extra_params""",
            (name, provider, model_id, temperature, max_tokens, vision_capable,
             supports_tools, json.dumps(extra_params) if extra_params else None,
             created_by, datetime.now())
        )
        await self._connection.commit()
    
    async def get_custom_model(self, name: str) -> Optional[Dict[str, Any]]:
        """Obtém um modelo customizado."""
        async with self._connection.execute(
            "SELECT * FROM custom_models WHERE name = ?",
            (name,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                data = dict(row)
                if data.get("extra_params"):
                    data["extra_params"] = json.loads(data["extra_params"])
                return data
            return None
    
    async def list_custom_models(self) -> List[Dict[str, Any]]:
        """Lista todos os modelos customizados."""
        async with self._connection.execute(
            "SELECT * FROM custom_models ORDER BY name"
        ) as cursor:
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                data = dict(row)
                if data.get("extra_params"):
                    data["extra_params"] = json.loads(data["extra_params"])
                result.append(data)
            return result
    
    async def delete_custom_model(self, name: str):
        """Deleta um modelo customizado."""
        await self._connection.execute(
            "DELETE FROM custom_models WHERE name = ?",
            (name,)
        )
        await self._connection.commit()
    
    # === Stats ===
    
    async def record_usage(
        self,
        user_id: int,
        guild_id: Optional[int],
        model: str,
        tokens_input: int = 0,
        tokens_output: int = 0,
        images_generated: int = 0
    ):
        """Registra uso do bot."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        await self._connection.execute(
            """INSERT INTO stats 
               (user_id, guild_id, model, date, tokens_input, tokens_output, 
                messages_sent, images_generated)
               VALUES (?, ?, ?, ?, ?, ?, 1, ?)
               ON CONFLICT(user_id, guild_id, model, date) DO UPDATE SET
               tokens_input = tokens_input + excluded.tokens_input,
               tokens_output = tokens_output + excluded.tokens_output,
               messages_sent = messages_sent + 1,
               images_generated = images_generated + excluded.images_generated""",
            (user_id, guild_id, model, today, tokens_input, tokens_output, images_generated)
        )
        await self._connection.commit()
    
    async def get_user_stats(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Obtém estatísticas de um usuário."""
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        async with self._connection.execute(
            """SELECT 
               SUM(tokens_input) as total_input,
               SUM(tokens_output) as total_output,
               SUM(messages_sent) as total_messages,
               SUM(images_generated) as total_images,
               COUNT(DISTINCT date) as active_days
               FROM stats 
               WHERE user_id = ? AND date >= ?""",
            (user_id, since)
        ) as cursor:
            row = await cursor.fetchone()
            return {
                "total_input_tokens": row[0] or 0,
                "total_output_tokens": row[1] or 0,
                "total_messages": row[2] or 0,
                "total_images": row[3] or 0,
                "active_days": row[4] or 0
            }
    
    # === Backup ===
    
    async def create_backup(self) -> str:
        """Cria um backup do banco de dados."""
        backup_dir = Path(self.db_path).parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"backup_{timestamp}.db"
        
        # Fechar conexão atual
        if self._connection:
            await self._connection.close()
        
        # Copiar arquivo
        shutil.copy2(self.db_path, backup_path)
        
        # Reabrir conexão
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        
        # Limpar backups antigos (manter últimos 10)
        backups = sorted(backup_dir.glob("backup_*.db"), key=lambda x: x.stat().st_mtime)
        for old_backup in backups[:-10]:
            old_backup.unlink()
        
        return str(backup_path)
    
    # === Guild Config ===
    
    async def create_guild_config(self, guild_id: int):
        """Cria configuração padrão para um servidor."""
        await self._connection.execute(
            """INSERT OR IGNORE INTO guild_settings (guild_id, created_at)
               VALUES (?, ?)""",
            (guild_id, datetime.now())
        )
        await self._connection.commit()
    
    async def get_guild_config(self, guild_id: int) -> Dict[str, Any]:
        """Obtém configuração de um servidor."""
        async with self._connection.execute(
            "SELECT * FROM guild_settings WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return {}
    
    async def update_guild_config(self, guild_id: int, **kwargs):
        """Atualiza configuração de um servidor."""
        fields = []
        values = []
        
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)
        
        if fields:
            values.extend([datetime.now(), guild_id])
            query = f"UPDATE guild_settings SET {', '.join(fields)}, updated_at = ? WHERE guild_id = ?"
            await self._connection.execute(query, values)
            await self._connection.commit()
    
    # === Active Effects (Shop Items) ===
    
    async def add_active_effect(
        self,
        user_id: int,
        channel_id: int,
        effect_type: str,
        effect_data: dict,
        duration_minutes: int
    ) -> int:
        """Adiciona um efeito ativo."""
        expires_at = datetime.now() + timedelta(minutes=duration_minutes)
        
        cursor = await self._connection.execute(
            """INSERT INTO active_effects 
               (user_id, channel_id, effect_type, effect_data, expires_at, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                channel_id,
                effect_type,
                json.dumps(effect_data),
                expires_at,
                datetime.now()
            )
        )
        await self._connection.commit()
        return cursor.lastrowid
    
    async def get_active_effects(
        self,
        channel_id: int,
        effect_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Obtém efeitos ativos em um canal."""
        if effect_type:
            async with self._connection.execute(
                """SELECT * FROM active_effects 
                   WHERE channel_id = ? AND effect_type = ? AND expires_at > ?
                   ORDER BY expires_at""",
                (channel_id, effect_type, datetime.now())
            ) as cursor:
                rows = await cursor.fetchall()
        else:
            async with self._connection.execute(
                """SELECT * FROM active_effects 
                   WHERE channel_id = ? AND expires_at > ?
                   ORDER BY expires_at""",
                (channel_id, datetime.now())
            ) as cursor:
                rows = await cursor.fetchall()
        
        result = []
        for row in rows:
            data = dict(row)
            if data.get("effect_data"):
                data["effect_data"] = json.loads(data["effect_data"])
            result.append(data)
        
        return result
    
    async def remove_expired_effects(self):
        """Remove efeitos expirados."""
        await self._connection.execute(
            "DELETE FROM active_effects WHERE expires_at <= ?",
            (datetime.now(),)
        )
        await self._connection.commit()
    
    async def remove_effect(self, effect_id: int):
        """Remove um efeito específico."""
        await self._connection.execute(
            "DELETE FROM active_effects WHERE id = ?",
            (effect_id,)
        )
        await self._connection.commit()
    
    # === DM Settings (Chat Privado) ===
    
    async def get_dm_settings(self, user_id: int) -> Dict[str, Any]:
        """Obtém configurações de DM de um usuário."""
        async with self._connection.execute(
            "SELECT * FROM dm_settings WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            
            # Criar configuração padrão
            await self._connection.execute(
                """INSERT INTO dm_settings (user_id, created_at)
                   VALUES (?, ?)""",
                (user_id, datetime.now())
            )
            await self._connection.commit()
            
            return await self.get_dm_settings(user_id)
    
    async def update_dm_settings(self, user_id: int, **kwargs):
        """Atualiza configurações de DM."""
        fields = []
        values = []
        
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)
        
        if fields:
            values.extend([datetime.now(), user_id])
            query = f"UPDATE dm_settings SET {', '.join(fields)}, updated_at = ? WHERE user_id = ?"
            await self._connection.execute(query, values)
            await self._connection.commit()
    
    async def clear_dm_context(self, user_id: int):
        """Limpa contexto de DM de um usuário."""
        # Limpar conversas
        await self._connection.execute(
            """DELETE FROM conversations 
               WHERE user_id = ? AND guild_id IS NULL""",
            (user_id,)
        )
        
        # Limpar memórias
        await self._connection.execute(
            "DELETE FROM memories WHERE context_id = ?",
            (f"dm_{user_id}",)
        )
        
        await self._connection.commit()
        )
        await self._connection.commit()
