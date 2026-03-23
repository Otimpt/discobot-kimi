"""
Sistema de Configuração Avançado
Suporta múltiplos provedores, modelos e variáveis de ambiente
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import yaml
from pathlib import Path


@dataclass
class ProviderConfig:
    """Configuração de um provedor de LLM."""
    name: str
    base_url: str
    api_key: str = ""
    extra_headers: Optional[Dict[str, str]] = None
    enabled: bool = True


@dataclass
class ModelConfig:
    """Configuração de um modelo específico."""
    name: str
    provider: str
    model_id: str
    temperature: float = 0.9
    max_tokens: int = 4096
    vision_capable: bool = False
    supports_tools: bool = True
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0


@dataclass
class MemoryConfig:
    """Configuração do sistema de memória."""
    enabled: bool = True
    retention_days: int = 180
    max_short_term_messages: int = 100
    context_window_minutes: int = 1440
    vector_store_type: str = "sqlite"  # sqlite, pinecone, qdrant, redis, pgvector
    embedding_model: str = "text-embedding-3-small"
    use_langcache: bool = False
    extract_facts: bool = True


@dataclass
class ImageGenerationConfig:
    """Configuração de geração de imagens."""
    enabled: bool = True
    provider: str = "openai"  # openai, together, stability
    model: str = "gpt-image-1"
    weekly_quota_default: int = 5
    max_quota_per_user: int = 50
    allowed_sizes: List[str] = field(default_factory=lambda: ["1024x1024", "1792x1024", "1024x1792"])


@dataclass
class TriggerConfig:
    """Configuração de gatilhos de resposta."""
    mode: str = "standard"  # standard, prefix, all, off
    prefix: str = "!"
    require_mention: bool = True
    require_reply: bool = True
    respond_to_bang: bool = False
    smart_interjection: bool = True
    interjection_sensitivity: str = "normal"  # low, normal, high


@dataclass
class ShopConfig:
    """Configuração da loja."""
    enabled: bool = True
    currency_name: str = "Tokens"
    currency_symbol: str = "🪙"
    starting_balance: int = 100
    items: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SafetyConfig:
    """Configuração de segurança/filtros."""
    mode: str = "standard"  # none, low, medium, standard, high, strict
    max_message_length: int = 2000
    block_keywords: List[str] = field(default_factory=list)
    allow_dm: bool = True


class Config:
    """Classe principal de configuração do bot."""
    
    # Mapeamento de variáveis de ambiente
    ENV_MAPPING = {
        "DISCORD_BOT_TOKEN": "bot_token",
        "DISCORD_CLIENT_ID": "client_id",
        "OPENAI_API_KEY": "providers.openai.api_key",
        "TOGETHER_API_KEY": "providers.together.api_key",
        "GROQ_API_KEY": "providers.groq.api_key",
        "OPENROUTER_API_KEY": "providers.openrouter.api_key",
        "XAI_API_KEY": "providers.xai.api_key",
        "MISTRAL_API_KEY": "providers.mistral.api_key",
        "COHERE_API_KEY": "providers.cohere.api_key",
        "ANTHROPIC_API_KEY": "providers.anthropic.api_key",
        "GOOGLE_API_KEY": "providers.google.api_key",
        "OPENAI_ASSISTANT_ID": "default_assistant_id",
        "GOOGLE_CSE_API_KEY": "google_cse_api_key",
        "GOOGLE_CSE_CX": "google_cse_cx",
        "PINECONE_API_KEY": "pinecone.api_key",
        "REDIS_URL": "redis.url",
        "SYSTEM_PROMPT": "system_prompt",
        "DB_PATH": "db_path",
    }
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = config_file
        self._config_data = {}
        
        # Carregar configuração
        self._load_yaml()
        self._apply_env_variables()
        self._setup_defaults()
        self._initialize_providers()
        self._initialize_models()
        
    def _load_yaml(self):
        """Carrega configuração do arquivo YAML."""
        config_path = Path(self.config_file)
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config_data = yaml.safe_load(f) or {}
        else:
            # Criar configuração padrão
            self._config_data = self._get_default_config()
            self._save_yaml()
    
    def _save_yaml(self):
        """Salva configuração atual no arquivo YAML."""
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.dump(self._config_data, f, default_flow_style=False, allow_unicode=True)
    
    def _apply_env_variables(self):
        """Aplica variáveis de ambiente sobre a configuração."""
        for env_var, config_path in self.ENV_MAPPING.items():
            value = os.getenv(env_var)
            if value:
                self._set_nested_value(config_path, value)
    
    def _set_nested_value(self, path: str, value: Any):
        """Define um valor aninhado no dicionário de configuração."""
        keys = path.split(".")
        current = self._config_data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
    
    def _get_nested_value(self, path: str, default: Any = None) -> Any:
        """Obtém um valor aninhado do dicionário de configuração."""
        keys = path.split(".")
        current = self._config_data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def _setup_defaults(self):
        """Configura valores padrão para todas as seções."""
        defaults = self._get_default_config()
        
        def merge_dicts(base, overlay):
            for key, value in overlay.items():
                if key not in base:
                    base[key] = value
                elif isinstance(value, dict) and isinstance(base[key], dict):
                    merge_dicts(base[key], value)
        
        merge_dicts(self._config_data, defaults)
    
    def _initialize_providers(self):
        """Inicializa configurações dos provedores."""
        self.providers: Dict[str, ProviderConfig] = {}
        
        provider_data = self._config_data.get("providers", {})
        for name, data in provider_data.items():
            self.providers[name] = ProviderConfig(
                name=name,
                base_url=data.get("base_url", ""),
                api_key=data.get("api_key", ""),
                extra_headers=data.get("extra_headers"),
                enabled=data.get("enabled", True)
            )
    
    def _initialize_models(self):
        """Inicializa configurações dos modelos."""
        self.models: Dict[str, ModelConfig] = {}
        
        model_data = self._config_data.get("models", {})
        for name, data in model_data.items():
            self.models[name] = ModelConfig(
                name=name,
                provider=data.get("provider", "openai"),
                model_id=data.get("model_id", name),
                temperature=data.get("temperature", 0.9),
                max_tokens=data.get("max_tokens", 4096),
                vision_capable=data.get("vision_capable", False),
                supports_tools=data.get("supports_tools", True),
                cost_per_1k_input=data.get("cost_per_1k_input", 0.0),
                cost_per_1k_output=data.get("cost_per_1k_output", 0.0)
            )
    
    def _get_default_config(self) -> Dict:
        """Retorna configuração padrão completa."""
        return {
            "bot_token": "",
            "client_id": "",
            "status_message": "🤖 IA Avançada | /ajuda",
            "status_type": "watching",  # playing, listening, watching, competing
            "db_path": "data/bot_database.db",
            "system_prompt": "Você é um assistente de IA amigável e prestativo.",
            "default_model": "gpt-4o-mini",
            "default_assistant_id": "",
            "max_text_length": 50000,
            "max_images_per_message": 5,
            "context_window_seconds": 86400,
            "backup_interval_minutes": 120,
            
            "providers": {
                "openai": {
                    "base_url": "https://api.openai.com/v1",
                    "api_key": "",
                    "enabled": True
                },
                "together": {
                    "base_url": "https://api.together.xyz/v1",
                    "api_key": "",
                    "enabled": False
                },
                "groq": {
                    "base_url": "https://api.groq.com/openai/v1",
                    "api_key": "",
                    "enabled": False
                },
                "openrouter": {
                    "base_url": "https://openrouter.ai/api/v1",
                    "api_key": "",
                    "extra_headers": {"X-Title": "Discord-AI-Bot"},
                    "enabled": False
                },
                "xai": {
                    "base_url": "https://api.x.ai/v1",
                    "api_key": "",
                    "enabled": False
                },
                "mistral": {
                    "base_url": "https://api.mistral.ai/v1",
                    "api_key": "",
                    "enabled": False
                },
                "cohere": {
                    "base_url": "https://api.cohere.ai/v1",
                    "api_key": "",
                    "enabled": False
                },
                "anthropic": {
                    "base_url": "https://api.anthropic.com/v1",
                    "api_key": "",
                    "enabled": False
                },
                "google": {
                    "base_url": "https://generativelanguage.googleapis.com/v1beta",
                    "api_key": "",
                    "enabled": False
                },
                "ollama": {
                    "base_url": "http://localhost:11434/v1",
                    "api_key": "ollama",
                    "enabled": False
                },
                "lmstudio": {
                    "base_url": "http://localhost:1234/v1",
                    "api_key": "lm-studio",
                    "enabled": False
                }
            },
            
            "models": {
                "gpt-4o": {
                    "provider": "openai",
                    "model_id": "gpt-4o",
                    "temperature": 0.9,
                    "max_tokens": 4096,
                    "vision_capable": True,
                    "supports_tools": True
                },
                "gpt-4o-mini": {
                    "provider": "openai",
                    "model_id": "gpt-4o-mini",
                    "temperature": 0.9,
                    "max_tokens": 4096,
                    "vision_capable": True,
                    "supports_tools": True
                },
                "gpt-5": {
                    "provider": "openai",
                    "model_id": "gpt-5",
                    "temperature": 0.9,
                    "max_tokens": 8192,
                    "vision_capable": True,
                    "supports_tools": True
                },
                "gpt-5-mini": {
                    "provider": "openai",
                    "model_id": "gpt-5-mini",
                    "temperature": 0.9,
                    "max_tokens": 4096,
                    "vision_capable": True,
                    "supports_tools": True
                },
                "claude-sonnet-4": {
                    "provider": "anthropic",
                    "model_id": "claude-sonnet-4-20250514",
                    "temperature": 0.9,
                    "max_tokens": 4096,
                    "vision_capable": True,
                    "supports_tools": True
                },
                "grok-3": {
                    "provider": "xai",
                    "model_id": "grok-3",
                    "temperature": 0.9,
                    "max_tokens": 4096,
                    "vision_capable": False,
                    "supports_tools": True
                },
                "llama-3.3-70b": {
                    "provider": "groq",
                    "model_id": "llama-3.3-70b-versatile",
                    "temperature": 0.9,
                    "max_tokens": 4096,
                    "vision_capable": False,
                    "supports_tools": True
                },
                "gemini-2.0-flash": {
                    "provider": "google",
                    "model_id": "gemini-2.0-flash",
                    "temperature": 0.9,
                    "max_tokens": 4096,
                    "vision_capable": True,
                    "supports_tools": True
                }
            },
            
            "memory": {
                "enabled": True,
                "retention_days": 180,
                "max_short_term_messages": 100,
                "context_window_minutes": 1440,
                "vector_store_type": "sqlite",
                "embedding_model": "text-embedding-3-small",
                "use_langcache": False,
                "extract_facts": True
            },
            
            "image_generation": {
                "enabled": True,
                "provider": "openai",
                "model": "gpt-image-1",
                "weekly_quota_default": 5,
                "max_quota_per_user": 50,
                "allowed_sizes": ["1024x1024", "1792x1024", "1024x1792"]
            },
            
            "triggers": {
                "mode": "standard",
                "prefix": "!",
                "require_mention": True,
                "require_reply": True,
                "respond_to_bang": False,
                "smart_interjection": True,
                "interjection_sensitivity": "normal"
            },
            
            "shop": {
                "enabled": True,
                "currency_name": "Tokens",
                "currency_symbol": "🪙",
                "starting_balance": 100,
                "items": {
                    "image_quota": {
                        "name": "Cota de Imagens (+5)",
                        "description": "Adicione 5 gerações de imagem à sua conta",
                        "cost": 50,
                        "effect": "add_image_quota",
                        "effect_value": 5
                    },
                    "summary": {
                        "name": "Resumo Premium",
                        "description": "Gere um resumo avançado de qualquer conversa",
                        "cost": 30,
                        "effect": "unlock_feature",
                        "effect_value": "premium_summary"
                    },
                    "memory_boost": {
                        "name": "Boost de Memória",
                        "description": "Aumente a retenção de memória por 7 dias",
                        "cost": 100,
                        "effect": "boost_memory",
                        "effect_value": 7
                    }
                }
            },
            
            "safety": {
                "mode": "standard",
                "max_message_length": 2000,
                "block_keywords": [],
                "allow_dm": True
            },
            
            "permissions": {
                "users": {
                    "allowed_ids": [],
                    "blocked_ids": []
                },
                "roles": {
                    "allowed_ids": [],
                    "blocked_ids": []
                },
                "channels": {
                    "allowed_ids": [],
                    "blocked_ids": []
                }
            },
            
            "admin_permissions": {
                "users": [],
                "roles": []
            },
            
            "google_cse_api_key": "",
            "google_cse_cx": "",
            
            "pinecone": {
                "api_key": "",
                "environment": "us-east-1",
                "index_name": "discord-bot-memory"
            },
            
            "redis": {
                "url": "redis://localhost:6379",
                "password": ""
            },
            
            "qdrant": {
                "url": "",
                "api_key": "",
                "collection_name": "discord-bot-memory"
            },
            
            "pgvector": {
                "host": "localhost",
                "port": 5432,
                "database": "botdb",
                "user": "botuser",
                "password": ""
            }
        }
    
    # Propriedades de acesso fácil
    @property
    def bot_token(self) -> str:
        return self._config_data.get("bot_token", "")
    
    @property
    def client_id(self) -> str:
        return self._config_data.get("client_id", "")
    
    @property
    def status_message(self) -> str:
        return self._config_data.get("status_message", "🤖 IA Avançada")
    
    @property
    def status_type(self) -> str:
        return self._config_data.get("status_type", "watching")
    
    @property
    def db_path(self) -> str:
        return self._config_data.get("db_path", "data/bot_database.db")
    
    @property
    def system_prompt(self) -> str:
        return self._config_data.get("system_prompt", "")
    
    @property
    def default_model(self) -> str:
        return self._config_data.get("default_model", "gpt-4o-mini")
    
    @property
    def default_assistant_id(self) -> str:
        return self._config_data.get("default_assistant_id", "")
    
    @property
    def memory_config(self) -> MemoryConfig:
        mem = self._config_data.get("memory", {})
        return MemoryConfig(
            enabled=mem.get("enabled", True),
            retention_days=mem.get("retention_days", 180),
            max_short_term_messages=mem.get("max_short_term_messages", 100),
            context_window_minutes=mem.get("context_window_minutes", 1440),
            vector_store_type=mem.get("vector_store_type", "sqlite"),
            embedding_model=mem.get("embedding_model", "text-embedding-3-small"),
            use_langcache=mem.get("use_langcache", False),
            extract_facts=mem.get("extract_facts", True)
        )
    
    @property
    def image_config(self) -> ImageGenerationConfig:
        img = self._config_data.get("image_generation", {})
        return ImageGenerationConfig(
            enabled=img.get("enabled", True),
            provider=img.get("provider", "openai"),
            model=img.get("model", "gpt-image-1"),
            weekly_quota_default=img.get("weekly_quota_default", 5),
            max_quota_per_user=img.get("max_quota_per_user", 50),
            allowed_sizes=img.get("allowed_sizes", ["1024x1024", "1792x1024", "1024x1792"])
        )
    
    @property
    def trigger_config(self) -> TriggerConfig:
        trig = self._config_data.get("triggers", {})
        return TriggerConfig(
            mode=trig.get("mode", "standard"),
            prefix=trig.get("prefix", "!"),
            require_mention=trig.get("require_mention", True),
            require_reply=trig.get("require_reply", True),
            respond_to_bang=trig.get("respond_to_bang", False),
            smart_interjection=trig.get("smart_interjection", True),
            interjection_sensitivity=trig.get("interjection_sensitivity", "normal")
        )
    
    @property
    def shop_config(self) -> ShopConfig:
        shop = self._config_data.get("shop", {})
        return ShopConfig(
            enabled=shop.get("enabled", True),
            currency_name=shop.get("currency_name", "Tokens"),
            currency_symbol=shop.get("currency_symbol", "🪙"),
            starting_balance=shop.get("starting_balance", 100),
            items=shop.get("items", {})
        )
    
    @property
    def safety_config(self) -> SafetyConfig:
        safety = self._config_data.get("safety", {})
        return SafetyConfig(
            mode=safety.get("mode", "standard"),
            max_message_length=safety.get("max_message_length", 2000),
            block_keywords=safety.get("block_keywords", []),
            allow_dm=safety.get("allow_dm", True)
        )
    
    def get_provider(self, name: str) -> Optional[ProviderConfig]:
        """Obtém configuração de um provedor específico."""
        return self.providers.get(name)
    
    def get_model(self, name: str) -> Optional[ModelConfig]:
        """Obtém configuração de um modelo específico."""
        return self.models.get(name)
    
    def add_model(self, name: str, config: Dict[str, Any]):
        """Adiciona um novo modelo dinamicamente."""
        self.models[name] = ModelConfig(name=name, **config)
        if "models" not in self._config_data:
            self._config_data["models"] = {}
        self._config_data["models"][name] = config
        self._save_yaml()
    
    def remove_model(self, name: str):
        """Remove um modelo."""
        if name in self.models:
            del self.models[name]
        if "models" in self._config_data and name in self._config_data["models"]:
            del self._config_data["models"][name]
            self._save_yaml()
    
    def save(self):
        """Salva configuração atual no arquivo."""
        self._save_yaml()
