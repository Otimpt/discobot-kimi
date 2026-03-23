"""
Gerenciador de Provedores LLM
Suporta múltiplos provedores com interface unificada
"""

from typing import Optional, Dict, Any, List, AsyncGenerator
import logging

from openai import AsyncOpenAI

from core.config import Config, ProviderConfig, ModelConfig

logger = logging.getLogger("discord-bot")


class ProviderManager:
    """Gerencia clientes de múltiplos provedores LLM."""
    
    def __init__(self, config: Config):
        self.config = config
        self._clients: Dict[str, AsyncOpenAI] = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Inicializa clientes para todos os provedores habilitados."""
        for name, provider in self.config.providers.items():
            if provider.enabled and provider.api_key:
                try:
                    self._clients[name] = AsyncOpenAI(
                        api_key=provider.api_key,
                        base_url=provider.base_url,
                        default_headers=provider.extra_headers
                    )
                    logger.info(f"✅ Provedor inicializado: {name}")
                except Exception as e:
                    logger.error(f"❌ Erro ao inicializar provedor {name}: {e}")
    
    def get_client(self, model_name: Optional[str] = None) -> AsyncOpenAI:
        """Obtém cliente para um modelo específico."""
        if not model_name:
            model_name = self.config.default_model
        
        # Extrair provedor do nome do modelo (formato: provedor/modelo)
        if "/" in model_name:
            provider_name = model_name.split("/")[0]
        else:
            # Tentar encontrar modelo na configuração
            model_config = self.config.get_model(model_name)
            if model_config:
                provider_name = model_config.provider
            else:
                provider_name = "openai"
        
        # Retornar cliente do provedor ou padrão
        if provider_name in self._clients:
            return self._clients[provider_name]
        
        if "openai" in self._clients:
            return self._clients["openai"]
        
        # Último recurso - criar cliente padrão
        return AsyncOpenAI()
    
    def get_model_id(self, model_name: str) -> str:
        """Obtém o ID real do modelo para a API."""
        model_config = self.config.get_model(model_name)
        if model_config:
            return model_config.model_id
        
        # Se tem formato provedor/modelo, retornar só o modelo
        if "/" in model_name:
            return model_name.split("/")[-1]
        
        return model_name
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Obtém configuração completa de um modelo."""
        return self.config.get_model(model_name)
    
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Faz uma chamada de chat completion."""
        client = self.get_client(model)
        model_id = self.get_model_id(model or self.config.default_model)
        model_config = self.get_model_config(model or self.config.default_model)
        
        # Usar valores da configuração se não especificados
        if temperature is None and model_config:
            temperature = model_config.temperature
        if max_tokens is None and model_config:
            max_tokens = model_config.max_tokens
        
        params = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature or 0.9,
            "max_tokens": max_tokens or 4096,
        }
        
        if tools and model_config and model_config.supports_tools:
            params["tools"] = tools
        
        try:
            if stream:
                return await client.chat.completions.create(**params, stream=True)
            else:
                response = await client.chat.completions.create(**params)
                return {
                    "content": response.choices[0].message.content,
                    "tool_calls": getattr(response.choices[0].message, 'tool_calls', None),
                    "usage": {
                        "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "output_tokens": response.usage.completion_tokens if response.usage else 0,
                    }
                }
        except Exception as e:
            logger.error(f"Erro na chamada LLM: {e}")
            raise
    
    async def streaming_completion(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Faz uma chamada de streaming."""
        client = self.get_client(model)
        model_id = self.get_model_id(model or self.config.default_model)
        
        try:
            stream = await client.chat.completions.create(
                model=model_id,
                messages=messages,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Erro no streaming: {e}")
            raise
    
    async def create_embedding(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        """Cria embedding para um texto."""
        client = self.get_client("openai")  # Embeddings geralmente usam OpenAI
        
        try:
            response = await client.embeddings.create(
                input=text[:8000],
                model=model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Erro ao criar embedding: {e}")
            # Retornar vetor zero em caso de erro
            return [0.0] * 1536
    
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid"
    ) -> Optional[str]:
        """Gera uma imagem usando DALL-E."""
        client = self.get_client("openai")
        
        try:
            response = await client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                style=style,
                n=1
            )
            return response.data[0].url
        except Exception as e:
            logger.error(f"Erro ao gerar imagem: {e}")
            return None
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """Lista todos os modelos disponíveis."""
        result = []
        
        for name, config in self.config.models.items():
            provider = self.config.get_provider(config.provider)
            result.append({
                "name": name,
                "provider": config.provider,
                "model_id": config.model_id,
                "enabled": provider.enabled if provider else False,
                "vision_capable": config.vision_capable,
                "supports_tools": config.supports_tools,
            })
        
        return result
    
    def add_provider(self, name: str, config: ProviderConfig):
        """Adiciona um novo provedor dinamicamente."""
        try:
            self._clients[name] = AsyncOpenAI(
                api_key=config.api_key,
                base_url=config.base_url,
                default_headers=config.extra_headers
            )
            logger.info(f"✅ Provedor adicionado: {name}")
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar provedor {name}: {e}")
            raise
