"""
Sistema de Memória Hierárquica Inteligente V2
Memória humana avançada com:
- Curto → Médio → Longo → Permanente
- Memórias podem pular etapas (direto para longo)
- Cross-server memory (chance rara de lembrar)
- Memórias permanentes (nunca esquecidas)
"""

import logging
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib

from core.memory_adapters import (
    MemoryAdapterFactory, BaseMemoryAdapter, SearchResult
)

logger = logging.getLogger("discord-bot")


class MemoryTier(Enum):
    """Camadas de memória."""
    SHORT_TERM = "short_term"       # 1-3 dias, todas as conversas
    MEDIUM_TERM = "medium_term"     # Resumos de curto prazo
    LONG_TERM = "long_term"         # 6+ meses, importantes (pode esquecer)
    PERMANENT = "permanent"         # NUNCA esquecido


class MemoryType(Enum):
    """Tipos de memória para categorização."""
    CONVERSATION = "conversation"   # Conversa normal
    FACT = "fact"                   # Fato importante
    JOKE = "joke"                   # Piada interna
    USER_INFO = "user_info"         # Informação sobre usuário
    SERVER_INFO = "server_info"     # Informação sobre servidor
    PREFERENCE = "preference"       # Preferência de alguém
    EVENT = "event"                 # Evento importante
    QUOTE = "quote"                 # Citação memorável
    RELATIONSHIP = "relationship"   # Relacionamento entre usuários
    LEARNED = "learned"             # Algo que o bot aprendeu


@dataclass
class MemoryEntry:
    """Uma entrada de memória inteligente."""
    id: str
    content: str
    timestamp: datetime
    tier: MemoryTier
    memory_type: MemoryType = MemoryType.CONVERSATION
    importance: float = 0.5          # 0.0-1.0
    access_count: int = 0            # Quanto foi acessada
    last_accessed: datetime = field(default_factory=datetime.now)
    
    # Origem
    source_guild_id: Optional[str] = None    # Servidor de origem
    source_channel_id: Optional[str] = None  # Canal de origem
    source_user_id: Optional[str] = None     # Usuário relacionado
    
    # Metadados
    summary: Optional[str] = None
    related_memories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    # Para memória permanente
    is_permanent: bool = False
    permanent_reason: Optional[str] = None
    permanent_since: Optional[datetime] = None
    
    # Para cross-server
    shared_with_guilds: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tier": self.tier.value,
            "memory_type": self.memory_type.value,
            "importance": self.importance,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat(),
            "source_guild_id": self.source_guild_id,
            "source_channel_id": self.source_channel_id,
            "source_user_id": self.source_user_id,
            "summary": self.summary,
            "related_memories": self.related_memories,
            "tags": self.tags,
            "metadata": self.metadata,
            "is_permanent": self.is_permanent,
            "permanent_reason": self.permanent_reason,
            "permanent_since": self.permanent_since.isoformat() if self.permanent_since else None,
            "shared_with_guilds": self.shared_with_guilds
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MemoryEntry':
        return cls(
            id=data["id"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            tier=MemoryTier(data["tier"]),
            memory_type=MemoryType(data.get("memory_type", "conversation")),
            importance=data.get("importance", 0.5),
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data.get("last_accessed", data["timestamp"])),
            source_guild_id=data.get("source_guild_id"),
            source_channel_id=data.get("source_channel_id"),
            source_user_id=data.get("source_user_id"),
            summary=data.get("summary"),
            related_memories=data.get("related_memories", []),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            is_permanent=data.get("is_permanent", False),
            permanent_reason=data.get("permanent_reason"),
            permanent_since=datetime.fromisoformat(data["permanent_since"]) if data.get("permanent_since") else None,
            shared_with_guilds=data.get("shared_with_guilds", [])
        )


class GuildMemorySystem:
    """
    Sistema de memória por servidor.
    Cada servidor tem suas próprias memórias isoladas.
    """
    
    # Chance de cross-server memory (muito rara!)
    CROSS_SERVER_CHANCE = 0.05  # 5% quando encontra alguém conhecido
    
    def __init__(
        self,
        db_manager,
        guild_id: str,
        config: Optional[Dict] = None
    ):
        self.db = db_manager
        self.guild_id = guild_id
        self.config = config or {}
        
        # Configurações
        self.short_term_days = self.config.get("short_term_days", 3)
        self.medium_term_days = self.config.get("medium_term_days", 14)
        self.long_term_months = self.config.get("long_term_months", 6)
        
        # Adapters
        self.adapters: Dict[MemoryTier, Optional[BaseMemoryAdapter]] = {
            MemoryTier.SHORT_TERM: None,
            MemoryTier.MEDIUM_TERM: None,
            MemoryTier.LONG_TERM: None,
            MemoryTier.PERMANENT: None
        }
        
        # Cache
        self._cache: Dict[str, MemoryEntry] = {}
        
        # Conhecidos (para cross-server)
        self._known_users: Set[str] = set()
        self._known_guilds: Set[str] = set()
    
    async def initialize(self):
        """Inicializa adapters."""
        providers = {
            MemoryTier.SHORT_TERM: self.config.get("short_term_provider", "sqlite"),
            MemoryTier.MEDIUM_TERM: self.config.get("medium_term_provider", "sqlite"),
            MemoryTier.LONG_TERM: self.config.get("long_term_provider", "sqlite"),
            MemoryTier.PERMANENT: self.config.get("permanent_provider", "sqlite")
        }
        
        for tier, provider in providers.items():
            try:
                config_key = f"{tier.value}_config"
                adapter_config = self.config.get(config_key, {})
                
                adapter = MemoryAdapterFactory.create_adapter(
                    provider,
                    **adapter_config
                )
                await adapter.initialize()
                self.adapters[tier] = adapter
                logger.info(f"[{self.guild_id}] Adapter {provider} inicializado para {tier.value}")
            except Exception as e:
                logger.error(f"[{self.guild_id}] Erro ao inicializar {provider}: {e}")
                # Fallback para SQLite
                try:
                    adapter = MemoryAdapterFactory.create_adapter("sqlite")
                    await adapter.initialize()
                    self.adapters[tier] = adapter
                except Exception as e2:
                    logger.error(f"Fallback também falhou: {e2}")
    
    async def add_memory(
        self,
        content: str,
        importance: float = 0.5,
        memory_type: MemoryType = MemoryType.CONVERSATION,
        user_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> MemoryEntry:
        """
        Adiciona uma nova memória.
        
        A memória pode ir direto para longo prazo se for importante o suficiente!
        """
        entry = MemoryEntry(
            id=self._generate_id(content, user_id),
            content=content,
            timestamp=datetime.now(),
            tier=MemoryTier.SHORT_TERM,  # Começa no curto prazo
            memory_type=memory_type,
            importance=importance,
            source_guild_id=self.guild_id,
            source_channel_id=channel_id,
            source_user_id=user_id,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Verificar se deve ir DIRETO para longo prazo (pula médio!)
        if self._should_go_direct_to_long_term(entry):
            entry.tier = MemoryTier.LONG_TERM
            logger.info(f"[{self.guild_id}] Memória foi DIRETO para longo prazo: {content[:50]}...")
        
        # Verificar se deve ser PERMANENTE
        if self._should_be_permanent(entry):
            entry.tier = MemoryTier.PERMANENT
            entry.is_permanent = True
            entry.permanent_reason = self._get_permanent_reason(entry)
            entry.permanent_since = datetime.now()
            logger.info(f"[{self.guild_id}] Memória PERMANENTE criada: {content[:50]}...")
        
        # Salvar
        await self._save_memory(entry)
        self._cache[entry.id] = entry
        
        # Adicionar usuário aos conhecidos
        if user_id:
            self._known_users.add(user_id)
        
        return entry
    
    def _should_go_direct_to_long_term(self, entry: MemoryEntry) -> bool:
        """Verifica se memória deve ir direto para longo prazo."""
        # Fatos importantes
        if entry.memory_type == MemoryType.FACT and entry.importance >= 0.8:
            return True
        
        # Informações sobre usuários (nome, aniversário, etc)
        if entry.memory_type == MemoryType.USER_INFO and entry.importance >= 0.7:
            return True
        
        # Informações do servidor
        if entry.memory_type == MemoryType.SERVER_INFO and entry.importance >= 0.75:
            return True
        
        # Piadas internas muito engraçadas
        if entry.memory_type == MemoryType.JOKE and entry.importance >= 0.85:
            return True
        
        # Eventos importantes
        if entry.memory_type == MemoryType.EVENT and entry.importance >= 0.8:
            return True
        
        # Preferências
        if entry.memory_type == MemoryType.PREFERENCE and entry.importance >= 0.7:
            return True
        
        # Citacoes memoráveis
        if entry.memory_type == MemoryType.QUOTE and entry.importance >= 0.8:
            return True
        
        # Qualquer coisa com importância muito alta
        if entry.importance >= 0.9:
            return True
        
        return False
    
    def _should_be_permanent(self, entry: MemoryEntry) -> bool:
        """Verifica se memória deve ser permanente."""
        # Já é permanente
        if entry.is_permanent:
            return True
        
        # Mencionada MUITAS vezes (virou tradição)
        if entry.access_count >= 20 and entry.importance >= 0.8:
            return True
        
        # Fato fundamental sobre o servidor
        if entry.memory_type == MemoryType.SERVER_INFO and entry.importance >= 0.95:
            return True
        
        # Relacionamento importante
        if entry.memory_type == MemoryType.RELATIONSHIP and entry.importance >= 0.9:
            return True
        
        # Qualquer coisa com importância máxima
        if entry.importance >= 0.95:
            return True
        
        return False
    
    def _get_permanent_reason(self, entry: MemoryEntry) -> str:
        """Retorna o motivo da memória ser permanente."""
        if entry.access_count >= 20:
            return f"Mencionada {entry.access_count} vezes - virou tradição!"
        
        if entry.memory_type == MemoryType.SERVER_INFO:
            return "Informação fundamental do servidor"
        
        if entry.memory_type == MemoryType.RELATIONSHIP:
            return "Relacionamento importante"
        
        return "Importância máxima"
    
    async def get_memories(
        self,
        query: Optional[str] = None,
        user_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        include_cross_server: bool = False
    ) -> List[MemoryEntry]:
        """
        Recupera memórias relevantes.
        
        Args:
            query: Busca por texto
            user_id: Filtrar por usuário
            memory_type: Filtrar por tipo
            limit: Limite de resultados
            include_cross_server: Incluir memórias de outros servidores (raro!)
        """
        memories = []
        
        # 1. Buscar em todas as camadas
        for tier in [MemoryTier.PERMANENT, MemoryTier.LONG_TERM, 
                     MemoryTier.MEDIUM_TERM, MemoryTier.SHORT_TERM]:
            tier_memories = await self._get_from_tier(
                tier, query, user_id, memory_type, limit
            )
            memories.extend(tier_memories)
        
        # 2. Cross-server memory (chance rara!)
        if include_cross_server and user_id:
            cross_memories = await self._try_cross_server_memory(user_id)
            if cross_memories:
                memories.extend(cross_memories)
        
        # 3. Ordenar por relevância
        memories.sort(key=lambda m: (
            m.importance * (1 + m.access_count * 0.1),
            m.last_accessed
        ), reverse=True)
        
        # 4. Atualizar acessos
        for mem in memories[:limit]:
            await self._update_access(mem)
        
        return memories[:limit]
    
    async def _try_cross_server_memory(self, user_id: str) -> List[MemoryEntry]:
        """
        Tenta recuperar memórias de outros servidores (chance rara!).
        
        Isso acontece quando o bot "reconhece" alguém de outro lugar
        e traz algumas memórias sutis.
        """
        # Verificar chance
        if random.random() > self.CROSS_SERVER_CHANCE:
            return []
        
        # Buscar memórias deste usuário em outros servidores
        cross_memories = []
        
        try:
            async with self.db._connection.execute(
                """SELECT * FROM memories 
                   WHERE source_user_id = ? 
                   AND source_guild_id != ?
                   AND tier IN ('long_term', 'permanent')
                   AND importance >= 0.7
                   ORDER BY importance DESC, access_count DESC
                   LIMIT 3""",
                (user_id, self.guild_id)
            ) as cursor:
                rows = await cursor.fetchall()
                
                for row in rows:
                    entry = MemoryEntry.from_dict(json.loads(row["data"]))
                    # Marcar como cross-server
                    entry.metadata["cross_server"] = True
                    entry.metadata["original_guild"] = entry.source_guild_id
                    cross_memories.append(entry)
                    
                    logger.info(
                        f"[{self.guild_id}] Cross-server memory ativada! "
                        f"Usuário {user_id} reconhecido de {entry.source_guild_id}"
                    )
        
        except Exception as e:
            logger.error(f"Erro cross-server memory: {e}")
        
        return cross_memories
    
    async def _get_from_tier(
        self,
        tier: MemoryTier,
        query: Optional[str],
        user_id: Optional[str],
        memory_type: Optional[MemoryType],
        limit: int
    ) -> List[MemoryEntry]:
        """Busca memórias em uma camada específica."""
        adapter = self.adapters.get(tier)
        if not adapter:
            return []
        
        # Buscar no adapter
        results = await adapter.search_memories(
            self.guild_id,
            query=query,
            limit=limit * 2  # Buscar mais para filtrar
        )
        
        memories = []
        for result in results:
            entry = MemoryEntry.from_dict(result.metadata)
            
            # Filtrar por usuário
            if user_id and entry.source_user_id != user_id:
                continue
            
            # Filtrar por tipo
            if memory_type and entry.memory_type != memory_type:
                continue
            
            # Verificar se não expirou (exceto permanente)
            if tier != MemoryTier.PERMANENT:
                if self._is_expired(entry, tier):
                    continue
            
            memories.append(entry)
        
        return memories
    
    def _is_expired(self, entry: MemoryEntry, tier: MemoryTier) -> bool:
        """Verifica se memória expirou."""
        if tier == MemoryTier.PERMANENT:
            return False
        
        if tier == MemoryTier.SHORT_TERM:
            cutoff = datetime.now() - timedelta(days=self.short_term_days)
            return entry.timestamp < cutoff
        
        if tier == MemoryTier.MEDIUM_TERM:
            cutoff = datetime.now() - timedelta(days=self.medium_term_days)
            return entry.timestamp < cutoff
        
        if tier == MemoryTier.LONG_TERM:
            # Longo prazo: apaga se não acessado em 6 meses
            cutoff = datetime.now() - timedelta(days=30 * self.long_term_months)
            return entry.last_accessed < cutoff
        
        return False
    
    async def _save_memory(self, entry: MemoryEntry):
        """Salva memória no adapter apropriado."""
        adapter = self.adapters.get(entry.tier)
        if adapter:
            await adapter.add_memory(
                self.guild_id,
                entry.id,
                entry.content,
                entry.to_dict()
            )
        
        # Também salvar no SQLite como backup
        await self.db._connection.execute(
            """INSERT OR REPLACE INTO memories 
               (id, context_id, tier, data, timestamp, last_accessed, importance, access_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.id,
                self.guild_id,
                entry.tier.value,
                json.dumps(entry.to_dict()),
                entry.timestamp,
                entry.last_accessed,
                entry.importance,
                entry.access_count
            )
        )
        await self.db._connection.commit()
    
    async def _update_access(self, entry: MemoryEntry):
        """Atualiza contador de acesso."""
        entry.access_count += 1
        entry.last_accessed = datetime.now()
        
        # Verificar promoção para permanente
        if not entry.is_permanent and self._should_be_permanent(entry):
            old_tier = entry.tier
            entry.tier = MemoryTier.PERMANENT
            entry.is_permanent = True
            entry.permanent_reason = f"Acessada {entry.access_count} vezes"
            entry.permanent_since = datetime.now()
            
            logger.info(
                f"[{self.guild_id}] Memória PROMOVIDA para PERMANENTE: "
                f"{entry.content[:50]}..."
            )
            
            # Mover para adapter permanente
            await self._promote_to_permanent(entry, old_tier)
        
        # Salvar atualização
        await self._save_memory(entry)
    
    async def _promote_to_permanent(self, entry: MemoryEntry, old_tier: MemoryTier):
        """Promove memória para permanente."""
        # Remover do tier antigo
        old_adapter = self.adapters.get(old_tier)
        if old_adapter:
            await old_adapter.delete_memory(self.guild_id, entry.id)
        
        # Adicionar ao permanente
        perm_adapter = self.adapters.get(MemoryTier.PERMANENT)
        if perm_adapter:
            await perm_adapter.add_memory(
                self.guild_id,
                entry.id,
                entry.content,
                entry.to_dict()
            )
    
    async def run_maintenance(self):
        """Executa manutenção das memórias."""
        logger.info(f"[{self.guild_id}] Iniciando manutenção de memória...")
        
        # 1. Consolidar curto → médio
        await self._consolidate_short_term()
        
        # 2. Promover médio → longo
        await self._promote_medium_to_long()
        
        # 3. Limpar expiradas
        await self._cleanup_expired()
        
        logger.info(f"[{self.guild_id}] Manutenção concluída.")
    
    async def _consolidate_short_term(self):
        """Resume memórias de curto prazo antigas."""
        adapter = self.adapters.get(MemoryTier.SHORT_TERM)
        if not adapter:
            return
        
        cutoff = datetime.now() - timedelta(days=self.short_term_days)
        
        # Buscar memórias antigas
        results = await adapter.search_memories(self.guild_id, limit=1000)
        
        to_summarize = []
        for result in results:
            entry = MemoryEntry.from_dict(result.metadata)
            if entry.timestamp < cutoff and not entry.is_permanent:
                to_summarize.append(entry)
        
        if len(to_summarize) >= 5:
            # Criar resumo
            summary_content = " | ".join([
                m.content[:100] for m in sorted(
                    to_summarize, 
                    key=lambda x: x.importance, 
                    reverse=True
                )[:5]
            ])
            
            summary_entry = MemoryEntry(
                id=f"summary_{self.guild_id}_{datetime.now().timestamp()}",
                content=summary_content,
                timestamp=datetime.now(),
                tier=MemoryTier.MEDIUM_TERM,
                memory_type=MemoryType.CONVERSATION,
                importance=max(m.importance for m in to_summarize),
                summary=f"Resumo de {len(to_summarize)} memórias",
                related_memories=[m.id for m in to_summarize]
            )
            
            await self._save_memory(summary_entry)
            
            # Deletar originais
            for mem in to_summarize:
                await adapter.delete_memory(self.guild_id, mem.id)
            
            logger.info(f"[{self.guild_id}] Resumidas {len(to_summarize)} memórias")
    
    async def _promote_medium_to_long(self):
        """Promove memórias de médio para longo prazo."""
        adapter = self.adapters.get(MemoryTier.MEDIUM_TERM)
        if not adapter:
            return
        
        results = await adapter.search_memories(self.guild_id, limit=1000)
        
        for result in results:
            entry = MemoryEntry.from_dict(result.metadata)
            
            # Critérios para promoção
            should_promote = (
                entry.access_count >= 5 or
                entry.importance >= 0.7 or
                entry.memory_type in [MemoryType.FACT, MemoryType.USER_INFO]
            )
            
            if should_promote:
                entry.tier = MemoryTier.LONG_TERM
                await self._save_memory(entry)
                await adapter.delete_memory(self.guild_id, entry.id)
                
                logger.debug(f"[{self.guild_id}] Promovido para longo: {entry.id[:8]}")
    
    async def _cleanup_expired(self):
        """Remove memórias expiradas."""
        for tier in [MemoryTier.SHORT_TERM, MemoryTier.MEDIUM_TERM, MemoryTier.LONG_TERM]:
            adapter = self.adapters.get(tier)
            if not adapter:
                continue
            
            results = await adapter.search_memories(self.guild_id, limit=1000)
            
            deleted = 0
            for result in results:
                entry = MemoryEntry.from_dict(result.metadata)
                if self._is_expired(entry, tier) and not entry.is_permanent:
                    await adapter.delete_memory(self.guild_id, entry.id)
                    deleted += 1
            
            if deleted > 0:
                logger.info(f"[{self.guild_id}] Apagadas {deleted} memórias de {tier.value}")
    
    def _generate_id(self, content: str, user_id: Optional[str]) -> str:
        """Gera ID único."""
        data = f"{content}:{self.guild_id}:{user_id}:{datetime.now().timestamp()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


class GlobalMemoryManager:
    """Gerenciador global de memória entre todos os servidores."""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.guild_systems: Dict[str, GuildMemorySystem] = {}
    
    async def get_guild_memory(
        self,
        guild_id: str,
        config: Optional[Dict] = None
    ) -> GuildMemorySystem:
        """Obtém sistema de memória de um servidor."""
        if guild_id not in self.guild_systems:
            self.guild_systems[guild_id] = GuildMemorySystem(
                db_manager=self.db,
                guild_id=guild_id,
                config=config
            )
            await self.guild_systems[guild_id].initialize()
        
        return self.guild_systems[guild_id]
    
    async def add_memory(
        self,
        guild_id: str,
        content: str,
        importance: float = 0.5,
        memory_type: str = "conversation",
        user_id: Optional[str] = None,
        **kwargs
    ) -> MemoryEntry:
        """Adiciona memória a um servidor."""
        system = await self.get_guild_memory(guild_id)
        
        return await system.add_memory(
            content=content,
            importance=importance,
            memory_type=MemoryType(memory_type),
            user_id=user_id,
            **kwargs
        )
    
    async def get_memories(
        self,
        guild_id: str,
        query: Optional[str] = None,
        user_id: Optional[str] = None,
        include_cross_server: bool = False,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """Recupera memórias de um servidor."""
        system = await self.get_guild_memory(guild_id)
        
        return await system.get_memories(
            query=query,
            user_id=user_id,
            include_cross_server=include_cross_server,
            limit=limit
        )
    
    async def run_maintenance_all(self):
        """Executa manutenção em todos os servidores."""
        for guild_id, system in self.guild_systems.items():
            try:
                await system.run_maintenance()
            except Exception as e:
                logger.error(f"Erro manutenção {guild_id}: {e}")
    
    async def close_all(self):
        """Fecha todos os sistemas."""
        for system in self.guild_systems.values():
            for adapter in system.adapters.values():
                if adapter:
                    try:
                        await adapter.close()
                    except:
                        pass


# Instância global
global_memory_manager: Optional[GlobalMemoryManager] = None


def setup_global_memory_manager(db_manager) -> GlobalMemoryManager:
    """Inicializa o gerenciador global de memória."""
    global global_memory_manager
    global_memory_manager = GlobalMemoryManager(db_manager)
    logger.info("Gerenciador global de memória inicializado")
    return global_memory_manager
