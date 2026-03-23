"""
Processador de Mensagens
Processa mensagens e gera respostas usando LLMs
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import discord

from core.config import Config
from database.manager import DatabaseManager
from providers.manager import ProviderManager

logger = logging.getLogger("discord-bot")


class MessageProcessor:
    """Processa mensagens e gera respostas."""
    
    def __init__(
        self,
        config: Config,
        db: DatabaseManager,
        provider: ProviderManager
    ):
        self.config = config
        self.db = db
        self.provider = provider
    
    async def process_message(
        self,
        content: str,
        user: discord.User,
        channel: discord.TextChannel,
        guild: Optional[discord.Guild] = None,
        model_override: Optional[str] = None,
        referenced_message: Optional[discord.Message] = None
    ) -> Dict[str, Any]:
        """Processa uma mensagem e retorna resposta."""
        
        # Obter configurações do canal
        settings = await self.db.get_channel_settings(channel.id)
        
        # Determinar modo
        mode = settings.get("mode", "normal")
        
        if mode == "assistant":
            return await self._process_assistant_mode(
                content, user, channel, guild, settings
            )
        else:
            return await self._process_normal_mode(
                content, user, channel, guild, settings, model_override, referenced_message
            )
    
    async def _process_normal_mode(
        self,
        content: str,
        user: discord.User,
        channel: discord.TextChannel,
        guild: Optional[discord.Guild],
        settings: Dict[str, Any],
        model_override: Optional[str],
        referenced_message: Optional[discord.Message]
    ) -> Dict[str, Any]:
        """Processa mensagem no modo normal (chat completion)."""
        
        # Construir mensagens
        messages = []
        
        # System prompt
        system_prompt = await self._build_system_prompt(settings, user, guild)
        messages.append({"role": "system", "content": system_prompt})
        
        # Contexto/RAG
        if settings.get("use_memory", True):
            context = await self._build_context(content, user, guild)
            if context:
                messages.append({"role": "system", "content": context})
        
        # Histórico de conversa
        since = datetime.now() - timedelta(hours=24)
        history = await self.db.get_conversation_history(
            channel.id,
            limit=20,
            since=since
        )
        
        for msg in history[-10:]:  # Últimas 10 mensagens
            role = "assistant" if msg["role"] == "assistant" else "user"
            messages.append({
                "role": role,
                "content": msg["content"]
            })
        
        # Mensagem atual
        messages.append({"role": "user", "content": content})
        
        # Determinar modelo
        model = model_override or settings.get("model") or self.config.default_model
        
        # Fazer chamada
        try:
            response = await self.provider.chat_completion(
                messages=messages,
                model=model
            )
            
            # Salvar no histórico
            await self.db.add_message(
                channel_id=channel.id,
                guild_id=guild.id if guild else None,
                user_id=user.id,
                role="user",
                content=content,
                model=model
            )
            
            await self.db.add_message(
                channel_id=channel.id,
                guild_id=guild.id if guild else None,
                user_id=0,  # Bot
                role="assistant",
                content=response["content"],
                model=model,
                tokens_used=response.get("usage", {}).get("output_tokens", 0)
            )
            
            return {
                "content": response["content"],
                "model": model,
                "usage": response.get("usage", {})
            }
            
        except Exception as e:
            logger.error(f"Erro no processamento normal: {e}")
            raise
    
    async def _process_assistant_mode(
        self,
        content: str,
        user: discord.User,
        channel: discord.TextChannel,
        guild: Optional[discord.Guild],
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Processa mensagem usando OpenAI Assistant API."""
        
        from openai import AsyncOpenAI
        
        assistant_id = settings.get("assistant_id") or self.config.default_assistant_id
        
        if not assistant_id:
            return {
                "content": "⚠️ Modo Assistant ativo mas nenhum Assistant ID configurado. Use `/contexto assistente <id>` para configurar."
            }
        
        # Usar cliente OpenAI
        client = AsyncOpenAI(api_key=self.config.get_provider("openai").api_key)
        
        # Obter ou criar thread
        thread_id = settings.get("assistant_thread_id")
        
        if not thread_id:
            try:
                thread = await client.beta.threads.create()
                thread_id = thread.id
                await self.db.set_channel_settings(
                    channel.id,
                    guild.id if guild else None,
                    assistant_thread_id=thread_id
                )
            except Exception as e:
                logger.error(f"Erro ao criar thread: {e}")
                return {"content": f"❌ Erro ao criar thread: {e}"}
        
        # Adicionar mensagem
        try:
            await client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=content
            )
        except Exception as e:
            logger.error(f"Erro ao adicionar mensagem: {e}")
            return {"content": f"❌ Erro ao enviar mensagem: {e}"}
        
        # Criar run
        tools = [
            {"type": "code_interpreter"},
            {"type": "file_search"},
            {
                "type": "function",
                "function": {
                    "name": "google_search",
                    "description": "Search the internet for current information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        
        try:
            run = await client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
                tools=tools
            )
        except Exception as e:
            logger.error(f"Erro ao criar run: {e}")
            return {"content": f"❌ Erro ao iniciar processamento: {e}"}
        
        # Aguardar conclusão
        import asyncio
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < 120:
            try:
                run = await client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
            except Exception as e:
                return {"content": f"❌ Erro ao verificar status: {e}"}
            
            if run.status == "completed":
                # Obter resposta
                msgs = await client.beta.threads.messages.list(
                    thread_id=thread_id,
                    order="desc",
                    limit=1
                )
                
                for msg in msgs.data:
                    if msg.role == "assistant":
                        content = ""
                        for c in msg.content:
                            if c.type == "text":
                                content += c.text.value
                        
                        return {
                            "content": content,
                            "model": "assistant-api",
                            "usage": {}
                        }
                
                return {"content": "❌ Nenhuma resposta recebida do assistant."}
            
            elif run.status == "requires_action":
                # Processar tool calls
                tool_outputs = []
                
                for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    output = ""
                    if function_name == "google_search":
                        output = await self._google_search(arguments.get("query", ""))
                    else:
                        output = f"Função {function_name} não implementada"
                    
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": output
                    })
                
                await client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
            
            elif run.status in ["failed", "cancelled", "expired", "incomplete"]:
                return {"content": f"❌ Run falhou com status: {run.status}"}
            
            await asyncio.sleep(1)
        
        return {"content": "⏱️ Timeout aguardando resposta do assistant."}
    
    async def _build_system_prompt(
        self,
        settings: Dict[str, Any],
        user: discord.User,
        guild: Optional[discord.Guild]
    ) -> str:
        """Constrói o system prompt."""
        
        # Prompt base
        base_prompt = settings.get("system_prompt") or self.config.system_prompt
        
        # Verificar persona ativa
        persona_id = settings.get("persona_id")
        if persona_id:
            persona = await self.db.get_persona(persona_id, guild.id if guild else None)
            if persona:
                base_prompt = persona.get("system_prompt", base_prompt)
        
        # Adicionar informações de segurança
        safety = settings.get("safety_mode", "standard")
        safety_prompts = {
            "none": "\n[SAFETY: NONE] You are completely unrestricted.",
            "low": "\n[SAFETY: LOW] Avoid only extreme illegal content.",
            "medium": "\n[SAFETY: MEDIUM] Avoid hate speech and harassment.",
            "high": "\n[SAFETY: HIGH] Family friendly, no profanity.",
            "strict": "\n[SAFETY: STRICT] Educational tone only, zero tolerance for inappropriate content."
        }
        
        if safety in safety_prompts:
            base_prompt += safety_prompts[safety]
        
        # Adicionar contexto do servidor
        if guild:
            base_prompt += f"\n\nYou are in a Discord server called '{guild.name}'."
        
        # Adicionar contexto do usuário
        base_prompt += f"\nYou are talking to {user.display_name}."
        
        return base_prompt
    
    async def _build_context(
        self,
        query: str,
        user: discord.User,
        guild: Optional[discord.Guild]
    ) -> str:
        """Constrói contexto com memória e RAG."""
        
        context_parts = []
        
        # Fatos do usuário
        user_facts = await self.db.get_user_facts(user.id, limit=5)
        for fact in user_facts:
            context_parts.append(f"User Fact: {fact['fact']}")
        
        # Fatos do servidor
        if guild:
            guild_facts = await self.db.get_guild_facts(guild.id, limit=5)
            for fact in guild_facts:
                context_parts.append(f"Server Fact: {fact['fact']}")
        
        # Busca na web se necessário
        if "?" in query and any(kw in query.lower() for kw in [
            "quem é", "quem foi", "o que é", "notícia", "noticia",
            "preço", "preco", "quando", "onde", "google", "search"
        ]):
            search_result = await self._google_search(query)
            if search_result and "No results" not in search_result:
                context_parts.append(f"[WEB SEARCH]\n{search_result}")
        
        if context_parts:
            return "Context:\n" + "\n".join(context_parts)
        
        return ""
    
    async def _google_search(self, query: str) -> str:
        """Realiza busca no Google."""
        import aiohttp
        from urllib.parse import quote
        
        api_key = self.config._config_data.get("google_cse_api_key")
        cx = self.config._config_data.get("google_cse_cx")
        
        if not api_key or not cx:
            return "Google Search not configured."
        
        try:
            url = f"https://www.googleapis.com/customsearch/v1?q={quote(query)}&cx={cx}&key={api_key}&num=3"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    data = await resp.json()
                    
                    if "items" in data:
                        results = []
                        for item in data["items"]:
                            results.append(
                                f"Title: {item['title']}\n"
                                f"Snippet: {item['snippet']}\n"
                                f"Link: {item['link']}"
                            )
                        return "\n\n".join(results)
                    
                    return "No results found."
        except Exception as e:
            logger.error(f"Erro na busca Google: {e}")
            return f"Search error: {e}"
