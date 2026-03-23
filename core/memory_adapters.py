"""
Adapters de Memória - Suporte a múltiplos provedores
Local: SQLite, Qdrant, Chroma, Weaviate, Milvus
Nuvem: Pinecone, Oracle, OpenAI, Cohere, Google
"""

import logging
import json
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger("discord-bot")


@dataclass
class SearchResult:
    """Resultado de busca na memória."""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any]


class BaseMemoryAdapter(ABC):
    """Classe base para adapters de memória."""
    
    def __init__(self, connection_string: Optional[str] = None, api_key: Optional[str] = None):
        self.connection_string = connection_string
        self.api_key = api_key
        self._initialized = False
    
    @abstractmethod
    async def initialize(self):
        """Inicializa a conexão."""
        pass
    
    @abstractmethod
    async def add_memory(
        self,
        context_id: str,
        memory_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Adiciona uma memória."""
        pass
    
    @abstractmethod
    async def search_memories(
        self,
        context_id: str,
        query: Optional[str] = None,
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """Busca memórias."""
        pass
    
    @abstractmethod
    async def get_memory(self, context_id: str, memory_id: str) -> Optional[SearchResult]:
        """Obtém uma memória específica."""
        pass
    
    @abstractmethod
    async def delete_memory(self, context_id: str, memory_id: str) -> bool:
        """Deleta uma memória."""
        pass
    
    @abstractmethod
    async def delete_old_memories(
        self,
        context_id: str,
        before: datetime,
        max_importance: float = 0.7
    ) -> int:
        """Remove memórias antigas."""
        pass
    
    @abstractmethod
    async def update_access(
        self,
        context_id: str,
        memory_id: str,
        access_count: int,
        last_accessed: datetime
    ) -> bool:
        """Atualiza contador de acesso."""
        pass
    
    @abstractmethod
    async def close(self):
        """Fecha a conexão."""
        pass
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Gera embedding simples (para adapters sem embedding nativo)."""
        # Embedding simples baseado em hash (não semântico, mas funcional)
        hash_val = hashlib.sha256(text.encode()).hexdigest()
        vec = [int(hash_val[i:i+2], 16) / 255.0 for i in range(0, 64, 2)]
        return vec


# ============================================================================
# ADAPTERS LOCAIS
# ============================================================================

class SQLiteAdapter(BaseMemoryAdapter):
    """Adapter para SQLite (padrão, sem embeddings)."""
    
    def __init__(self, db_path: str = "data/memory.db", **kwargs):
        super().__init__(**kwargs)
        self.db_path = db_path
        self._connection = None
    
    async def initialize(self):
        """Inicializa SQLite."""
        import aiosqlite
        from pathlib import Path
        
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        
        # Criar tabelas
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT,
                context_id TEXT,
                content TEXT,
                metadata TEXT,
                created_at TIMESTAMP,
                last_accessed TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                PRIMARY KEY (id, context_id)
            )
        """)
        
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_context 
            ON memories(context_id, created_at)
        """)
        
        await self._connection.commit()
        self._initialized = True
        logger.info(f"SQLite adapter inicializado: {self.db_path}")
    
    async def add_memory(
        self,
        context_id: str,
        memory_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> bool:
        try:
            await self._connection.execute(
                """INSERT OR REPLACE INTO memories 
                   (id, context_id, content, metadata, created_at, last_accessed, access_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    memory_id, context_id, content, json.dumps(metadata),
                    datetime.now(), datetime.now(), metadata.get("access_count", 0)
                )
            )
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Erro SQLite add_memory: {e}")
            return False
    
    async def search_memories(
        self,
        context_id: str,
        query: Optional[str] = None,
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        try:
            if query:
                # Busca por texto (LIKE)
                async with self._connection.execute(
                    """SELECT * FROM memories 
                       WHERE context_id = ? AND content LIKE ?
                       ORDER BY created_at DESC
                       LIMIT ?""",
                    (context_id, f"%{query}%", limit)
                ) as cursor:
                    rows = await cursor.fetchall()
            else:
                # Busca recente
                async with self._connection.execute(
                    """SELECT * FROM memories 
                       WHERE context_id = ?
                       ORDER BY created_at DESC
                       LIMIT ?""",
                    (context_id, limit)
                ) as cursor:
                    rows = await cursor.fetchall()
            
            results = []
            for row in rows:
                metadata = json.loads(row["metadata"])
                results.append(SearchResult(
                    id=row["id"],
                    content=row["content"],
                    score=1.0,  # SQLite não tem score de similaridade
                    metadata=metadata
                ))
            return results
        except Exception as e:
            logger.error(f"Erro SQLite search_memories: {e}")
            return []
    
    async def get_memory(self, context_id: str, memory_id: str) -> Optional[SearchResult]:
        try:
            async with self._connection.execute(
                "SELECT * FROM memories WHERE context_id = ? AND id = ?",
                (context_id, memory_id)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    metadata = json.loads(row["metadata"])
                    return SearchResult(
                        id=row["id"],
                        content=row["content"],
                        score=1.0,
                        metadata=metadata
                    )
                return None
        except Exception as e:
            logger.error(f"Erro SQLite get_memory: {e}")
            return None
    
    async def delete_memory(self, context_id: str, memory_id: str) -> bool:
        try:
            await self._connection.execute(
                "DELETE FROM memories WHERE context_id = ? AND id = ?",
                (context_id, memory_id)
            )
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Erro SQLite delete_memory: {e}")
            return False
    
    async def delete_old_memories(
        self,
        context_id: str,
        before: datetime,
        max_importance: float = 0.7
    ) -> int:
        try:
            cursor = await self._connection.execute(
                """DELETE FROM memories 
                   WHERE context_id = ? 
                   AND created_at < ?
                   AND (
                       json_extract(metadata, '$.importance') IS NULL
                       OR json_extract(metadata, '$.importance') < ?
                   )""",
                (context_id, before, max_importance)
            )
            await self._connection.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Erro SQLite delete_old_memories: {e}")
            return 0
    
    async def update_access(
        self,
        context_id: str,
        memory_id: str,
        access_count: int,
        last_accessed: datetime
    ) -> bool:
        try:
            await self._connection.execute(
                """UPDATE memories 
                   SET access_count = ?, last_accessed = ?
                   WHERE context_id = ? AND id = ?""",
                (access_count, last_accessed, context_id, memory_id)
            )
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error(f"Erro SQLite update_access: {e}")
            return False
    
    async def close(self):
        if self._connection:
            await self._connection.close()


class QdrantAdapter(BaseMemoryAdapter):
    """Adapter para Qdrant (local ou nuvem)."""
    
    def __init__(self, 
                 host: Optional[str] = None, 
                 port: Optional[int] = None,
                 url: Optional[str] = None,
                 api_key: Optional[str] = None,
                 **kwargs):
        super().__init__(**kwargs)
        
        # Qdrant Cloud usa URL + API key
        # Qdrant local usa host + port
        self.host = host
        self.port = port
        self.url = url
        self.api_key = api_key
        self._client = None
        self._is_cloud = url is not None and api_key is not None
    
    async def initialize(self):
        """Inicializa Qdrant (local ou cloud)."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            # Conectar (cloud ou local)
            if self._is_cloud:
                self._client = QdrantClient(
                    url=self.url,
                    api_key=self.api_key
                )
                logger.info(f"Qdrant Cloud conectado: {self.url}")
            else:
                host = self.host or "localhost"
                port = self.port or 6333
                self._client = QdrantClient(host=host, port=port)
                logger.info(f"Qdrant Local conectado: {host}:{port}")
            
            # Criar coleção se não existir
            collections = self._client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if "bot_memories" not in collection_names:
                self._client.create_collection(
                    collection_name="bot_memories",
                    vectors_config=VectorParams(size=32, distance=Distance.COSINE)
                )
                logger.info("Coleção 'bot_memories' criada no Qdrant")
            
            self._initialized = True
            
        except ImportError:
            logger.warning("Qdrant não instalado. Use: pip install qdrant-client")
            raise
        except Exception as e:
            logger.error(f"Erro ao inicializar Qdrant: {e}")
            raise
    
    async def add_memory(
        self,
        context_id: str,
        memory_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> bool:
        try:
            from qdrant_client.models import PointStruct
            
            embedding = self._generate_embedding(content)
            
            point = PointStruct(
                id=f"{context_id}_{memory_id}",
                vector=embedding,
                payload={
                    "context_id": context_id,
                    "memory_id": memory_id,
                    "content": content,
                    **metadata
                }
            )
            
            self._client.upsert(
                collection_name="bot_memories",
                points=[point]
            )
            return True
        except Exception as e:
            logger.error(f"Erro Qdrant add_memory: {e}")
            return False
    
    async def search_memories(
        self,
        context_id: str,
        query: Optional[str] = None,
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        try:
            if query:
                # Busca por similaridade
                query_vector = self._generate_embedding(query)
                results = self._client.search(
                    collection_name="bot_memories",
                    query_vector=query_vector,
                    query_filter={
                        "must": [{"key": "context_id", "match": {"value": context_id}}]
                    },
                    limit=limit
                )
            else:
                # Scroll para pegar recentes
                results, _ = self._client.scroll(
                    collection_name="bot_memories",
                    scroll_filter={
                        "must": [{"key": "context_id", "match": {"value": context_id}}]
                    },
                    limit=limit
                )
            
            return [
                SearchResult(
                    id=r.payload["memory_id"],
                    content=r.payload["content"],
                    score=r.score if hasattr(r, 'score') else 1.0,
                    metadata={k: v for k, v in r.payload.items() 
                             if k not in ["context_id", "memory_id", "content"]}
                )
                for r in results
            ]
        except Exception as e:
            logger.error(f"Erro Qdrant search_memories: {e}")
            return []
    
    async def get_memory(self, context_id: str, memory_id: str) -> Optional[SearchResult]:
        try:
            results = self._client.retrieve(
                collection_name="bot_memories",
                ids=[f"{context_id}_{memory_id}"]
            )
            if results:
                r = results[0]
                return SearchResult(
                    id=r.payload["memory_id"],
                    content=r.payload["content"],
                    score=1.0,
                    metadata={k: v for k, v in r.payload.items() 
                             if k not in ["context_id", "memory_id", "content"]}
                )
            return None
        except Exception as e:
            logger.error(f"Erro Qdrant get_memory: {e}")
            return None
    
    async def delete_memory(self, context_id: str, memory_id: str) -> bool:
        try:
            self._client.delete(
                collection_name="bot_memories",
                points_selector=[f"{context_id}_{memory_id}"]
            )
            return True
        except Exception as e:
            logger.error(f"Erro Qdrant delete_memory: {e}")
            return False
    
    async def delete_old_memories(
        self,
        context_id: str,
        before: datetime,
        max_importance: float = 0.7
    ) -> int:
        # Qdrant não suporta deleção por data diretamente
        # Precisaria buscar e deletar manualmente
        logger.warning("Qdrant delete_old_memories não implementado completamente")
        return 0
    
    async def update_access(self, context_id: str, memory_id: str, 
                           access_count: int, last_accessed: datetime) -> bool:
        try:
            self._client.set_payload(
                collection_name="bot_memories",
                payload={"access_count": access_count, "last_accessed": last_accessed.isoformat()},
                points=[f"{context_id}_{memory_id}"]
            )
            return True
        except Exception as e:
            logger.error(f"Erro Qdrant update_access: {e}")
            return False
    
    async def close(self):
        pass  # Qdrant client não precisa de close explícito


class ChromaAdapter(BaseMemoryAdapter):
    """Adapter para ChromaDB (vector store local)."""
    
    def __init__(self, persist_directory: str = "data/chroma", **kwargs):
        super().__init__(**kwargs)
        self.persist_directory = persist_directory
        self._client = None
    
    async def initialize(self):
        """Inicializa ChromaDB."""
        try:
            import chromadb
            from chromadb.config import Settings
            
            self._client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.persist_directory
            ))
            
            # Criar/get coleção
            self._collection = self._client.get_or_create_collection(
                name="bot_memories",
                metadata={"hnsw:space": "cosine"}
            )
            
            self._initialized = True
            logger.info(f"Chroma adapter inicializado: {self.persist_directory}")
        
        except ImportError:
            logger.warning("ChromaDB não instalado. Use: pip install chromadb")
            raise
    
    async def add_memory(
        self,
        context_id: str,
        memory_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> bool:
        try:
            embedding = self._generate_embedding(content)
            
            self._collection.add(
                ids=[f"{context_id}_{memory_id}"],
                embeddings=[embedding],
                documents=[content],
                metadatas=[{**metadata, "context_id": context_id}]
            )
            return True
        except Exception as e:
            logger.error(f"Erro Chroma add_memory: {e}")
            return False
    
    async def search_memories(
        self,
        context_id: str,
        query: Optional[str] = None,
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        try:
            if query:
                query_embedding = self._generate_embedding(query)
                results = self._collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit,
                    where={"context_id": context_id}
                )
            else:
                results = self._collection.get(
                    where={"context_id": context_id},
                    limit=limit
                )
            
            search_results = []
            if query:
                for i, doc_id in enumerate(results["ids"][0]):
                    search_results.append(SearchResult(
                        id=doc_id.replace(f"{context_id}_", ""),
                        content=results["documents"][0][i],
                        score=results["distances"][0][i] if results["distances"] else 1.0,
                        metadata=results["metadatas"][0][i]
                    ))
            else:
                for i, doc_id in enumerate(results["ids"]):
                    search_results.append(SearchResult(
                        id=doc_id.replace(f"{context_id}_", ""),
                        content=results["documents"][i],
                        score=1.0,
                        metadata=results["metadatas"][i]
                    ))
            
            return search_results
        except Exception as e:
            logger.error(f"Erro Chroma search_memories: {e}")
            return []
    
    async def get_memory(self, context_id: str, memory_id: str) -> Optional[SearchResult]:
        try:
            result = self._collection.get(
                ids=[f"{context_id}_{memory_id}"]
            )
            if result and result["ids"]:
                return SearchResult(
                    id=memory_id,
                    content=result["documents"][0],
                    score=1.0,
                    metadata=result["metadatas"][0]
                )
            return None
        except Exception as e:
            logger.error(f"Erro Chroma get_memory: {e}")
            return None
    
    async def delete_memory(self, context_id: str, memory_id: str) -> bool:
        try:
            self._collection.delete(ids=[f"{context_id}_{memory_id}"])
            return True
        except Exception as e:
            logger.error(f"Erro Chroma delete_memory: {e}")
            return False
    
    async def delete_old_memories(
        self,
        context_id: str,
        before: datetime,
        max_importance: float = 0.7
    ) -> int:
        logger.warning("Chroma delete_old_memories não implementado completamente")
        return 0
    
    async def update_access(self, context_id: str, memory_id: str,
                           access_count: int, last_accessed: datetime) -> bool:
        try:
            self._collection.update(
                ids=[f"{context_id}_{memory_id}"],
                metadatas=[{"access_count": access_count, "last_accessed": last_accessed.isoformat()}]
            )
            return True
        except Exception as e:
            logger.error(f"Erro Chroma update_access: {e}")
            return False
    
    async def close(self):
        pass


# ============================================================================
# ADAPTERS NUVEM
# ============================================================================

class PineconeAdapter(BaseMemoryAdapter):
    """Adapter para Pinecone (nuvem)."""
    
    def __init__(self, api_key: str, environment: str = "us-west1-gcp", **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        self.environment = environment
        self._index = None
    
    async def initialize(self):
        """Inicializa Pinecone."""
        try:
            import pinecone
            
            pinecone.init(api_key=self.api_key, environment=self.environment)
            
            # Criar índice se não existir
            if "bot-memories" not in pinecone.list_indexes():
                pinecone.create_index(
                    name="bot-memories",
                    dimension=32,
                    metric="cosine"
                )
            
            self._index = pinecone.Index("bot-memories")
            self._initialized = True
            logger.info("Pinecone adapter inicializado")
        
        except ImportError:
            logger.warning("Pinecone não instalado. Use: pip install pinecone-client")
            raise
    
    async def add_memory(
        self,
        context_id: str,
        memory_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> bool:
        try:
            embedding = self._generate_embedding(content)
            
            self._index.upsert([
                {
                    "id": f"{context_id}_{memory_id}",
                    "values": embedding,
                    "metadata": {
                        "context_id": context_id,
                        "memory_id": memory_id,
                        "content": content,
                        **metadata
                    }
                }
            ])
            return True
        except Exception as e:
            logger.error(f"Erro Pinecone add_memory: {e}")
            return False
    
    async def search_memories(
        self,
        context_id: str,
        query: Optional[str] = None,
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        try:
            if query:
                query_vector = self._generate_embedding(query)
                results = self._index.query(
                    vector=query_vector,
                    top_k=limit,
                    filter={"context_id": {"$eq": context_id}},
                    include_metadata=True
                )
            else:
                # Pinecone não tem scroll, usar query com vetor zero
                results = self._index.query(
                    vector=[0.0] * 32,
                    top_k=limit,
                    filter={"context_id": {"$eq": context_id}},
                    include_metadata=True
                )
            
            return [
                SearchResult(
                    id=match["metadata"]["memory_id"],
                    content=match["metadata"]["content"],
                    score=match["score"],
                    metadata={k: v for k, v in match["metadata"].items()
                             if k not in ["context_id", "memory_id", "content"]}
                )
                for match in results["matches"]
            ]
        except Exception as e:
            logger.error(f"Erro Pinecone search_memories: {e}")
            return []
    
    async def get_memory(self, context_id: str, memory_id: str) -> Optional[SearchResult]:
        try:
            result = self._index.fetch([f"{context_id}_{memory_id}"])
            if result and result["vectors"]:
                vec = result["vectors"][f"{context_id}_{memory_id}"]
                return SearchResult(
                    id=memory_id,
                    content=vec["metadata"]["content"],
                    score=1.0,
                    metadata={k: v for k, v in vec["metadata"].items()
                             if k not in ["context_id", "memory_id", "content"]}
                )
            return None
        except Exception as e:
            logger.error(f"Erro Pinecone get_memory: {e}")
            return None
    
    async def delete_memory(self, context_id: str, memory_id: str) -> bool:
        try:
            self._index.delete(ids=[f"{context_id}_{memory_id}"])
            return True
        except Exception as e:
            logger.error(f"Erro Pinecone delete_memory: {e}")
            return False
    
    async def delete_old_memories(
        self,
        context_id: str,
        before: datetime,
        max_importance: float = 0.7
    ) -> int:
        logger.warning("Pinecone delete_old_memories não implementado")
        return 0
    
    async def update_access(self, context_id: str, memory_id: str,
                           access_count: int, last_accessed: datetime) -> bool:
        # Pinecone não suporta update parcial fácil
        logger.warning("Pinecone update_access requer re-upsert")
        return True
    
    async def close(self):
        pass


class RedisAdapter(BaseMemoryAdapter):
    """Adapter para Redis (cache rápido)."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, 
                 password: Optional[str] = None, db: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self._client = None
    
    async def initialize(self):
        """Inicializa Redis."""
        try:
            import redis.asyncio as redis
            
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                decode_responses=True
            )
            
            await self._client.ping()
            self._initialized = True
            logger.info(f"Redis adapter inicializado: {self.host}:{self.port}")
        
        except ImportError:
            logger.warning("Redis não instalado. Use: pip install redis")
            raise
    
    async def add_memory(
        self,
        context_id: str,
        memory_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> bool:
        try:
            key = f"memory:{context_id}:{memory_id}"
            data = {
                "content": content,
                "metadata": json.dumps(metadata),
                "created_at": datetime.now().isoformat()
            }
            
            await self._client.hset(key, mapping=data)
            # Expira em 7 dias (cache)
            await self._client.expire(key, 7 * 24 * 60 * 60)
            
            return True
        except Exception as e:
            logger.error(f"Erro Redis add_memory: {e}")
            return False
    
    async def search_memories(
        self,
        context_id: str,
        query: Optional[str] = None,
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        try:
            # Redis não tem busca por conteúdo nativamente
            # Listar todas as chaves do contexto
            pattern = f"memory:{context_id}:*"
            keys = await self._client.keys(pattern)
            
            results = []
            for key in keys[:limit]:
                data = await self._client.hgetall(key)
                if data:
                    memory_id = key.split(":")[-1]
                    results.append(SearchResult(
                        id=memory_id,
                        content=data.get("content", ""),
                        score=1.0,
                        metadata=json.loads(data.get("metadata", "{}"))
                    ))
            
            return results
        except Exception as e:
            logger.error(f"Erro Redis search_memories: {e}")
            return []
    
    async def get_memory(self, context_id: str, memory_id: str) -> Optional[SearchResult]:
        try:
            key = f"memory:{context_id}:{memory_id}"
            data = await self._client.hgetall(key)
            
            if data:
                return SearchResult(
                    id=memory_id,
                    content=data.get("content", ""),
                    score=1.0,
                    metadata=json.loads(data.get("metadata", "{}"))
                )
            return None
        except Exception as e:
            logger.error(f"Erro Redis get_memory: {e}")
            return None
    
    async def delete_memory(self, context_id: str, memory_id: str) -> bool:
        try:
            key = f"memory:{context_id}:{memory_id}"
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Erro Redis delete_memory: {e}")
            return False
    
    async def delete_old_memories(
        self,
        context_id: str,
        before: datetime,
        max_importance: float = 0.7
    ) -> int:
        # Redis expira automaticamente
        return 0
    
    async def update_access(self, context_id: str, memory_id: str,
                           access_count: int, last_accessed: datetime) -> bool:
        try:
            key = f"memory:{context_id}:{memory_id}"
            metadata = await self._client.hget(key, "metadata")
            if metadata:
                meta = json.loads(metadata)
                meta["access_count"] = access_count
                meta["last_accessed"] = last_accessed.isoformat()
                await self._client.hset(key, "metadata", json.dumps(meta))
            return True
        except Exception as e:
            logger.error(f"Erro Redis update_access: {e}")
            return False
    
    async def close(self):
        if self._client:
            await self._client.close()


# ============================================================================
# FACTORY
# ============================================================================

class MemoryAdapterFactory:
    """Factory para criar adapters de memória."""
    
    ADAPTERS = {
        "sqlite": SQLiteAdapter,
        "qdrant": QdrantAdapter,
        "chroma": ChromaAdapter,
        "pinecone": PineconeAdapter,
        "redis": RedisAdapter,
    }
    
    @classmethod
    def create_adapter(
        cls,
        provider: str,
        **kwargs
    ) -> BaseMemoryAdapter:
        """Cria um adapter para o provedor especificado."""
        provider = provider.lower()
        
        if provider not in cls.ADAPTERS:
            raise ValueError(f"Provedor não suportado: {provider}. "
                           f"Disponíveis: {list(cls.ADAPTERS.keys())}")
        
        adapter_class = cls.ADAPTERS[provider]
        return adapter_class(**kwargs)
    
    @classmethod
    def register_adapter(cls, name: str, adapter_class: type):
        """Registra um novo adapter."""
        cls.ADAPTERS[name.lower()] = adapter_class
        logger.info(f"Adapter registrado: {name}")
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """Lista provedores disponíveis."""
        return list(cls.ADAPTERS.keys())


# Instância global
adapter_factory = MemoryAdapterFactory()
