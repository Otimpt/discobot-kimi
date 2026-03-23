"""
Sistema de Memória Hierárquica Inteligente
Funciona como a memória humana: curto → médio → longo prazo
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib

from core.memory_adapters import (
    MemoryAdapterFactory, BaseMemoryAdapter, SearchResult
)

logger = logging.getLogger("discord-bot")


class MemoryTier(Enum):
    """Camadas de memória."""
    SHORT_TERM = "short_term"      # 1-3 dias
    MEDIUM_TERM = "medium_term"    # Resumos de curto prazo
    LONG_TERM = "long_term"        # 6+ meses (apaga se não usada)


class MemoryProvider(Enum):
    """Provedores de memória disponíveis."""
    # LOCAIS
    SQLITE = "sqlite"              # Padrão - SQLite simples
    QDRANT = "qdrant"              # Vector store local (recomendado)
    CHROMA = "chroma"              # ChromaDB local
    WEAVIATE = "weaviate"          # Weaviate local
    MILVUS = "milvus"              # Milvus local
    
    # NUVEM
    PINECONE = "pinecone"          # Pinecone (nuvem)
    ORACLE = "oracle"              # Oracle Cloud
    
    # CACHE
    REDIS = "redis"                # Redis (cache rápido)
    
    # EMBEDDINGS COM IA
    OPENAI = "openai"              # OpenAI Embeddings + qualquer DB
    COHERE = "cohere"              # Cohere Embeddings + qualquer DB
    GOOGLE = "google"              # Google Vertex AI Embeddings


@dataclass
class MemoryConfig:
    """Configuração de memória por camada."""
    provider: MemoryProvider
    connection_string: Optional[str] = None
    api_key: Optional[str] = None
    extra_params: Dict = field(default_factory=dict)


@dataclass
class MemoryEntry:
    """Uma entrada de memória."""
    id: str
    content: str
    timestamp: datetime
    tier: MemoryTier
    importance: float = 0.5          # 0.0-1.0
    access_count: int = 0            # Quanto foi acessada
    last_accessed: datetime = field(default_factory=datetime.now)
    summary: Optional[str] = None    # Resumo (para médio/longo prazo)
    related_memories: List[str] = field(default_factory=list)
    source: str = "conversation"     # Origem da memória
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tier": self.tier.value,
            "importance": self.importance,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat(),
            "summary": self.summary,
            "related_memories": self.related_memories,
            "source": self.source,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MemoryEntry':
        return cls(
            id=data["id"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            tier=MemoryTier(data["tier"]),
            importance=data.get("importance", 0.5),
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data.get("last_accessed", data["timestamp"])),
            summary=data.get("summary"),
            related_memories=data.get("related_memories", []),
            source=data.get("source", "conversation"),
            metadata=data.get("metadata", {})
        )
    
    @classmethod
    def from_search_result(cls, result: SearchResult, tier: MemoryTier) -> 'MemoryEntry':
        """Cria MemoryEntry de SearchResult."""
        return cls(
            id=result.id,
            content=result.content,
            timestamp=datetime.fromisoformat(result.metadata.get("timestamp", datetime.now().isoformat())),
            tier=tier,
            importance=result.metadata.get("importance", 0.5),
            access_count=result.metadata.get("access_count", 0),
            last_accessed=datetime.fromisoformat(result.metadata.get("last_accessed", datetime.now().isoformat())),
            metadata=result.metadata
        )


class HierarchicalMemorySystem:
    """
    Sistema de memória hierárquica que imita a memória humana.
    
    - Curto prazo: Conversas recentes (1-3 dias)
    - Médio prazo: Resumos de curto prazo, acessados ocasionalmente
    - Longo prazo: Memórias importantes, mantidas por 6+ meses
    """
    
    def __init__(
        self,
        db_manager,
        context_id: str,
        short_term_days: int = 3,
        long_term_months: int = 6,
        short_term_provider: MemoryProvider = MemoryProvider.SQLITE,
        medium_term_provider: MemoryProvider = MemoryProvider.SQLITE,
        long_term_provider: MemoryProvider = MemoryProvider.SQLITE,
        short_term_config: Optional[Dict] = None,
        medium_term_config: Optional[Dict] = None,
        long_term_config: Optional[Dict] = None
    ):
        self.db = db_manager
        self.context_id = context_id
        self.short_term_days = short_term_days
        self.long_term_months = long_term_months
        
        # Adapters para cada camada
        self.adapters: Dict[MemoryTier, Optional[BaseMemoryAdapter]] = {
            MemoryTier.SHORT_TERM: None,
            MemoryTier.MEDIUM_TERM: None,
            MemoryTier.LONG_TERM: None
        }
        
        # Configurações
        self.provider_configs = {
            MemoryTier.SHORT_TERM: short_term_config or {},
            MemoryTier.MEDIUM_TERM: medium_term_config or {},
            MemoryTier.LONG_TERM: long_term_config or {}
        }
        
        self.providers = {
            MemoryTier.SHORT_TERM: short_term_provider,
            MemoryTier.MEDIUM_TERM: medium_term_provider,
            MemoryTier.LONG_TERM: long_term_provider
        }
        
        # Cache em memória para curto prazo
        self._short_term_cache: Dict[str, MemoryEntry] = {}
        
        logger.info(
            f"Sistema de memória inicializado para {context_id}:\n"
            f"  - Curto prazo: {short_term_days} dias ({short_term_provider.value})\n"
            f"  - Médio prazo: Resumos ({medium_term_provider.value})\n"
            f"  - Longo prazo: {long_term_months} meses ({long_term_provider.value})"
        )
    
    async def initialize_adapters(self):
        """Inicializa os adapters de memória."""
        for tier in MemoryTier:
            provider = self.providers[tier]
            config = self.provider_configs[tier]
            
            try:
                adapter = MemoryAdapterFactory.create_adapter(
                    provider.value,
                    **config
                )
                await adapter.initialize()
                self.adapters[tier] = adapter
                logger.info(f"Adapter {provider.value} inicializado para {tier.value}")
            except Exception as e:
                logger.error(f"Erro ao inicializar {provider.value} para {tier.value}: {e}")
                # Fallback para SQLite
                if provider != MemoryProvider.SQLITE:
                    logger.warning(f"Fallback para SQLite em {tier.value}")
                    try:
                        adapter = MemoryAdapterFactory.create_adapter("sqlite")
                        await adapter.initialize()
                        self.adapters[tier] = adapter
                    except Exception as e2:
                        logger.error(f"Fallback também falhou: {e2}")
    
    # === Operações Principais ===
    
    async def add_memory(
        self,
        content: str,
        importance: float = 0.5,
        source: str = "conversation",
        metadata: Optional[Dict] = None
    ) -> MemoryEntry:
        """
        Adiciona uma nova memória (sempre começa no curto prazo).
        
        Args:
            content: Conteúdo da memória
            importance: Importância (0.0-1.0)
            source: Origem da memória
            metadata: Metadados adicionais
        """
        entry = MemoryEntry(
            id=self._generate_id(content),
            content=content,
            timestamp=datetime.now(),
            tier=MemoryTier.SHORT_TERM,
            importance=importance,
            source=source,
            metadata=metadata or {}
        )
        
        # Salvar no adapter de curto prazo
        adapter = self.adapters.get(MemoryTier.SHORT_TERM)
        if adapter:
            await adapter.add_memory(
                self.context_id,
                entry.id,
                entry.content,
                entry.to_dict()
            )
        
        # Adicionar ao cache
        self._short_term_cache[entry.id] = entry
        
        # Também salvar no SQLite como backup
        await self._save_to_sqlite(entry)
        
        logger.debug(f"Memória adicionada: {entry.id[:8]}... (importância: {importance})")
        
        return entry
    
    async def get_relevant_memories(
        self,
        query: Optional[str] = None,
        limit: int = 10,
        include_all_tiers: bool = True
    ) -> List[MemoryEntry]:
        """
        Recupera memórias relevantes.
        
        Prioridade:
        1. Curto prazo (recentes)
        2. Médio prazo (resumos relevantes)
        3. Longo prazo (importantes)
        """
        memories = []
        
        # 1. Curto prazo (sempre incluído)
        short_term = await self._get_short_term_memories(query, limit // 2)
        memories.extend(short_term)
        
        if include_all_tiers and len(memories) < limit:
            # 2. Médio prazo (resumos)
            medium_term = await self._get_medium_term_memories(
                query,
                limit - len(memories)
            )
            memories.extend(medium_term)
            
            # 3. Longo prazo (importantes)
            if len(memories) < limit:
                long_term = await self._get_long_term_memories(
                    query,
                    limit - len(memories)
                )
                memories.extend(long_term)
        
        # Atualizar contadores de acesso
        for mem in memories:
            await self._update_access_count(mem)
        
        return memories[:limit]
    
    async def search_memories(
        self,
        keywords: List[str],
        limit: int = 5
    ) -> List[MemoryEntry]:
        """Busca memórias por palavras-chave."""
        all_memories = await self.get_relevant_memories(limit=100)
        
        # Filtrar por keywords
        results = []
        for mem in all_memories:
            content_lower = mem.content.lower()
            if any(kw.lower() in content_lower for kw in keywords):
                results.append(mem)
        
        # Ordenar por relevância
        results.sort(key=lambda m: m.importance * (1 + m.access_count * 0.1), reverse=True)
        
        return results[:limit]
    
    # === Manutenção de Memória ===
    
    async def process_memory_maintenance(self):
        """
        Processo de manutenção periódica:
        1. Resumir memórias de curto prazo antigas
        2. Mover resumos para médio prazo
        3. Consolidar memórias importantes para longo prazo
        4. Apagar memórias antigas não usadas
        """
        logger.info(f"Iniciando manutenção de memória para {self.context_id}...")
        
        # 1. Processar curto prazo → médio prazo
        await self._consolidate_short_term()
        
        # 2. Processar médio prazo → longo prazo
        await self._consolidate_medium_term()
        
        # 3. Limpar memórias antigas de longo prazo
        await self._cleanup_long_term()
        
        logger.info(f"Manutenção de memória concluída para {self.context_id}.")
    
    async def _consolidate_short_term(self):
        """Resume memórias de curto prazo antigas."""
        cutoff = datetime.now() - timedelta(days=self.short_term_days)
        
        adapter = self.adapters.get(MemoryTier.SHORT_TERM)
        if not adapter:
            return
        
        # Buscar memórias antigas
        old_memories = await adapter.search_memories(
            self.context_id,
            limit=100
        )
        
        # Filtrar por data
        to_summarize = []
        for result in old_memories:
            created = datetime.fromisoformat(result.metadata.get("timestamp", datetime.now().isoformat()))
            if created < cutoff:
                to_summarize.append(result)
        
        if len(to_summarize) >= 5:
            summary = await self._create_summary(to_summarize)
            
            # Criar entrada de médio prazo
            medium_entry = MemoryEntry(
                id=f"summary_{self.context_id}_{datetime.now().timestamp()}",
                content=summary,
                timestamp=datetime.now(),
                tier=MemoryTier.MEDIUM_TERM,
                importance=max(m.metadata.get("importance", 0.5) for m in to_summarize),
                summary=f"Resumo de {len(to_summarize)} memórias",
                related_memories=[m.id for m in to_summarize],
                source="summary"
            )
            
            # Salvar em médio prazo
            medium_adapter = self.adapters.get(MemoryTier.MEDIUM_TERM)
            if medium_adapter:
                await medium_adapter.add_memory(
                    self.context_id,
                    medium_entry.id,
                    medium_entry.content,
                    medium_entry.to_dict()
                )
            
            # Deletar originais
            for mem in to_summarize:
                await adapter.delete_memory(self.context_id, mem.id)
            
            logger.info(f"Resumidas {len(to_summarize)} memórias para {self.context_id}")
    
    async def _consolidate_medium_term(self):
        """Move memórias importantes de médio para longo prazo."""
        adapter = self.adapters.get(MemoryTier.MEDIUM_TERM)
        if not adapter:
            return
        
        # Buscar memórias muito acessadas
        results = await adapter.search_memories(self.context_id, limit=100)
        
        for result in results:
            access_count = result.metadata.get("access_count", 0)
            importance = result.metadata.get("importance", 0.5)
            
            if access_count >= 5 and importance >= 0.6:
                # Mover para longo prazo
                long_adapter = self.adapters.get(MemoryTier.LONG_TERM)
                if long_adapter:
                    await long_adapter.add_memory(
                        self.context_id,
                        result.id,
                        result.content,
                        {**result.metadata, "promoted_at": datetime.now().isoformat()}
                    )
                
                # Deletar do médio prazo
                await adapter.delete_memory(self.context_id, result.id)
                
                logger.debug(f"Memória promovida para longo prazo: {result.id[:8]}...")
    
    async def _cleanup_long_term(self):
        """Remove memórias de longo prazo não usadas."""
        cutoff = datetime.now() - timedelta(days=30 * self.long_term_months)
        
        adapter = self.adapters.get(MemoryTier.LONG_TERM)
        if not adapter:
            return
        
        deleted = await adapter.delete_old_memories(
            self.context_id,
            cutoff,
            max_importance=0.7
        )
        
        if deleted > 0:
            logger.info(f"Removidas {deleted} memórias antigas de longo prazo")
    
    # === Métodos Auxiliares ===
    
    async def _create_summary(self, memories: List[SearchResult]) -> str:
        """Cria um resumo de múltiplas memórias."""
        key_points = []
        for mem in memories:
            if mem.metadata.get("importance", 0.5) > 0.5:
                key_points.append(mem.content[:100] + "...")
        
        if not key_points:
            key_points = [m.content[:50] + "..." for m in memories[:3]]
        
        return " | ".join(key_points)
    
    def _generate_id(self, content: str) -> str:
        """Gera ID único para memória."""
        data = f"{content}:{self.context_id}:{datetime.now().timestamp()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    async def _save_to_sqlite(self, entry: MemoryEntry):
        """Salva memória no SQLite como backup."""
        await self.db._connection.execute(
            """INSERT OR REPLACE INTO memories 
               (id, context_id, tier, data, timestamp, last_accessed, importance, access_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.id,
                self.context_id,
                entry.tier.value,
                json.dumps(entry.to_dict()),
                entry.timestamp,
                entry.last_accessed,
                entry.importance,
                entry.access_count
            )
        )
        await self.db._connection.commit()
    
    async def _get_short_term_memories(
        self,
        query: Optional[str] = None,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """Obtém memórias de curto prazo."""
        adapter = self.adapters.get(MemoryTier.SHORT_TERM)
        if not adapter:
            return []
        
        # Verificar cache primeiro
        if not query and self._short_term_cache:
            cache_entries = sorted(
                self._short_term_cache.values(),
                key=lambda m: m.timestamp,
                reverse=True
            )[:limit]
            return cache_entries
        
        # Buscar no adapter
        results = await adapter.search_memories(self.context_id, query, limit)
        
        return [MemoryEntry.from_search_result(r, MemoryTier.SHORT_TERM) for r in results]
    
    async def _get_medium_term_memories(
        self,
        query: Optional[str] = None,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """Obtém resumos de médio prazo."""
        adapter = self.adapters.get(MemoryTier.MEDIUM_TERM)
        if not adapter:
            return []
        
        results = await adapter.search_memories(self.context_id, query, limit)
        return [MemoryEntry.from_search_result(r, MemoryTier.MEDIUM_TERM) for r in results]
    
    async def _get_long_term_memories(
        self,
        query: Optional[str] = None,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """Obtém memórias importantes de longo prazo."""
        adapter = self.adapters.get(MemoryTier.LONG_TERM)
        if not adapter:
            return []
        
        results = await adapter.search_memories(self.context_id, query, limit)
        
        # Filtrar por importância
        important = [r for r in results if r.metadata.get("importance", 0.5) >= 0.6]
        
        return [MemoryEntry.from_search_result(r, MemoryTier.LONG_TERM) for r in important[:limit]]
    
    async def _update_access_count(self, entry: MemoryEntry):
        """Atualiza contador de acesso."""
        entry.access_count += 1
        entry.last_accessed = datetime.now()
        
        # Atualizar no adapter
        for tier in MemoryTier:
            adapter = self.adapters.get(tier)
            if adapter:
                await adapter.update_access(
                    self.context_id,
                    entry.id,
                    entry.access_count,
                    entry.last_accessed
                )
        
        # Atualizar no SQLite
        await self.db._connection.execute(
            """UPDATE memories 
               SET access_count = ?, last_accessed = ?
               WHERE id = ? AND context_id = ?""",
            (entry.access_count, entry.last_accessed, entry.id, self.context_id)
        )
        await self.db._connection.commit()
    
    async def close(self):
        """Fecha todos os adapters."""
        for tier, adapter in self.adapters.items():
            if adapter:
                try:
                    await adapter.close()
                    logger.info(f"Adapter {tier.value} fechado")
                except Exception as e:
                    logger.error(f"Erro ao fechar adapter {tier.value}: {e}")


class MemoryManager:
    """Gerenciador global de memória."""
    
    # CONFIGURAÇÃO PADRÃO
    DEFAULT_CONFIG = {
        "short_term_days": 3,
        "long_term_months": 6,
        "short_term_provider": MemoryProvider.SQLITE,  # Padrão: SQLite
        "medium_term_provider": MemoryProvider.SQLITE,  # Padrão: SQLite
        "long_term_provider": MemoryProvider.SQLITE,    # Padrão: SQLite
    }
    
    # CONFIGURAÇÃO RECOMENDADA (com Qdrant)
    RECOMMENDED_CONFIG = {
        "short_term_days": 3,
        "long_term_months": 6,
        "short_term_provider": MemoryProvider.QDRANT,
        "medium_term_provider": MemoryProvider.QDRANT,
        "long_term_provider": MemoryProvider.QDRANT,
        "short_term_config": {"host": "localhost", "port": 6333},
        "medium_term_config": {"host": "localhost", "port": 6333},
        "long_term_config": {"host": "localhost", "port": 6333},
    }
    
    # CONFIGURAÇÃO NUVEM (com Pinecone)
    CLOUD_CONFIG = {
        "short_term_days": 3,
        "long_term_months": 6,
        "short_term_provider": MemoryProvider.PINECONE,
        "medium_term_provider": MemoryProvider.PINECONE,
        "long_term_provider": MemoryProvider.PINECONE,
        "short_term_config": {"api_key": "SUA_API_KEY", "environment": "us-west1-gcp"},
        "medium_term_config": {"api_key": "SUA_API_KEY", "environment": "us-west1-gcp"},
        "long_term_config": {"api_key": "SUA_API_KEY", "environment": "us-west1-gcp"},
    }
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.systems: Dict[str, HierarchicalMemorySystem] = {}
        self._configs: Dict[str, Dict] = {}
    
    async def get_memory_system(
        self,
        context_id: str,
        config: Optional[Dict] = None
    ) -> HierarchicalMemorySystem:
        """Obtém ou cria sistema de memória para um contexto."""
        if context_id not in self.systems:
            cfg = {**self.DEFAULT_CONFIG, **(config or {})}
            
            # Converter strings para enums
            for key in ["short_term_provider", "medium_term_provider", "long_term_provider"]:
                if isinstance(cfg[key], str):
                    cfg[key] = MemoryProvider(cfg[key])
            
            self._configs[context_id] = cfg
            
            self.systems[context_id] = HierarchicalMemorySystem(
                db_manager=self.db,
                context_id=context_id,
                short_term_days=cfg["short_term_days"],
                long_term_months=cfg["long_term_months"],
                short_term_provider=cfg["short_term_provider"],
                medium_term_provider=cfg["medium_term_provider"],
                long_term_provider=cfg["long_term_provider"],
                short_term_config=cfg.get("short_term_config"),
                medium_term_config=cfg.get("medium_term_config"),
                long_term_config=cfg.get("long_term_config")
            )
            
            # Inicializar adapters
            await self.systems[context_id].initialize_adapters()
        
        return self.systems[context_id]
    
    async def configure_memory(
        self,
        context_id: str,
        tier: MemoryTier,
        provider: MemoryProvider,
        connection_string: Optional[str] = None,
        api_key: Optional[str] = None,
        extra_params: Optional[Dict] = None
    ):
        """Configura provedor de memória para uma camada."""
        config_key = f"{tier.value}_provider"
        config_extra = f"{tier.value}_config"
        
        # Atualizar config
        if context_id not in self._configs:
            self._configs[context_id] = dict(self.DEFAULT_CONFIG)
        
        self._configs[context_id][config_key] = provider
        self._configs[context_id][config_extra] = {
            "connection_string": connection_string,
            "api_key": api_key,
            **(extra_params or {})
        }
        
        # Salvar no banco
        await self.db._connection.execute(
            """INSERT OR REPLACE INTO memory_config 
               (context_id, tier, provider, connection_string, api_key, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (context_id, tier.value, provider.value, connection_string, api_key, datetime.now())
        )
        await self.db._connection.commit()
        
        # Recriar sistema se existir
        if context_id in self.systems:
            await self.systems[context_id].close()
            del self.systems[context_id]
        
        logger.info(f"Memória configurada para {context_id}: {tier.value} → {provider.value}")
    
    async def load_config_from_db(self, context_id: str) -> Dict:
        """Carrega configuração do banco."""
        async with self.db._connection.execute(
            "SELECT * FROM memory_config WHERE context_id = ?",
            (context_id,)
        ) as cursor:
            rows = await cursor.fetchall()
        
        config = dict(self.DEFAULT_CONFIG)
        
        for row in rows:
            tier = row["tier"]
            provider = MemoryProvider(row["provider"])
            
            config[f"{tier}_provider"] = provider
            config[f"{tier}_config"] = {
                "connection_string": row.get("connection_string"),
                "api_key": row.get("api_key")
            }
        
        return config
    
    async def run_maintenance(self):
        """Executa manutenção em todos os sistemas."""
        logger.info("Iniciando manutenção global de memória...")
        
        for context_id, system in self.systems.items():
            try:
                await system.process_memory_maintenance()
            except Exception as e:
                logger.error(f"Erro na manutenção de {context_id}: {e}")
        
        logger.info("Manutenção global concluída.")
    
    async def close_all(self):
        """Fecha todos os sistemas."""
        for context_id, system in self.systems.items():
            try:
                await system.close()
            except Exception as e:
                logger.error(f"Erro ao fechar sistema {context_id}: {e}")
        
        self.systems.clear()


# Instância global
memory_manager: Optional[MemoryManager] = None


def setup_memory_manager(db_manager) -> MemoryManager:
    """Inicializa o gerenciador de memória."""
    global memory_manager
    memory_manager = MemoryManager(db_manager)
    logger.info("Gerenciador de memória inicializado")
    return memory_manager
