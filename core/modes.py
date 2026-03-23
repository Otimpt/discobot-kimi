"""
Sistema de Modos de Operação do Bot
Define como o bot se comporta em diferentes modos
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List


class BotMode(Enum):
    """Modos de operação do bot."""
    
    # Modo Normal - Chat completion padrão
    NORMAL = "normal"
    
    # Modo Assistant - OpenAI Assistant API
    ASSISTANT = "assistant"
    
    # Modo Chatbot - Responde sem gatilhos, IA decide quando responder
    CHATBOT = "chatbot"
    
    # Modo Interativo - Membro do servidor com personalidade complexa
    INTERACTIVE = "interactive"
    
    # Modo Roleplay - Persona ativa com comportamento específico
    ROLEPLAY = "roleplay"


class TriggerType(Enum):
    """Tipos de gatilhos de resposta."""
    
    # SEMPRE ativo - responde em reply às mensagens do bot
    REPLY = "reply"
    
    # Responde quando mencionado (@Bot)
    MENTION = "mention"
    
    # Responde quando usa prefixo (!comando)
    PREFIX = "prefix"
    
    # Responde quando mensagem começa com ?
    QUESTION = "question"
    
    # Combinação: prefixo OU menção
    BOTH = "both"


@dataclass
class TriggerConfig:
    """Configuração de gatilhos."""
    
    # Reply SEMPRE funciona (não é configurável)
    reply_always: bool = True
    
    # Menção (@Bot)
    on_mention: bool = True
    
    # Prefixo configurável (padrão: !)
    on_prefix: bool = False
    prefix: str = "!"
    
    # Interrogação (?)
    on_question: bool = False
    
    # Modo "ambos" - prefixo OU menção
    on_both: bool = False
    
    # Sensibilidade do modo chatbot
    chatbot_sensitivity: str = "normal"  # low, normal, high


@dataclass
class ModeConfig:
    """Configuração de um modo de operação."""
    
    name: str
    description: str
    icon: str
    system_prompt_suffix: str
    features: List[str]
    editable: bool  # Se pode ser alterado pelo usuário


# Configurações dos modos
MODE_CONFIGS = {
    BotMode.NORMAL: ModeConfig(
        name="Normal",
        description="Chat completion padrão com histórico",
        icon="💬",
        system_prompt_suffix="",
        features=["memory", "context", "tools"],
        editable=True
    ),
    
    BotMode.ASSISTANT: ModeConfig(
        name="Assistant API",
        description="OpenAI Assistant com ferramentas avançadas",
        icon="🤖",
        system_prompt_suffix="Você tem acesso a ferramentas avançadas.",
        features=["code_interpreter", "file_search", "functions", "threads"],
        editable=True
    ),
    
    BotMode.CHATBOT: ModeConfig(
        name="Chatbot",
        description="Responde automaticamente sem precisar de gatilhos",
        icon="🎯",
        system_prompt_suffix="Você é um chatbot que participa ativamente das conversas.",
        features=["auto_reply", "smart_interjection", "context_aware"],
        editable=True
    ),
    
    BotMode.INTERACTIVE: ModeConfig(
        name="Interativo",
        description="Membro do servidor com personalidade complexa e memória",
        icon="👤",
        system_prompt_suffix="""Você é um membro ativo deste servidor Discord. 
        Você tem uma personalidade única, gostos, opiniões e memórias próprias. 
        Você não é apenas um assistente, mas alguém que faz parte da comunidade.
        Responda de forma natural, como uma pessoa real faria.
        Às vezes você concorda, às vezes discorda. Você tem bom humor.
        Você lembra de conversas passadas e menciona coisas que aprendeu sobre as pessoas.""",
        features=[
            "evolving_personality", 
            "long_term_memory", 
            "preferences",
            "opinions",
            "relationships",
            "emotional_memory",
            "context_awareness"
        ],
        editable=False  # Modo interativo tem configuração própria
    ),
    
    BotMode.ROLEPLAY: ModeConfig(
        name="Roleplay",
        description="Persona específica com comportamento definido",
        icon="🎭",
        system_prompt_suffix="Você está interpretando um personagem específico.",
        features=["persona", "character_consistency", "thematic_responses"],
        editable=True
    )
}


def get_mode_config(mode: BotMode) -> ModeConfig:
    """Retorna configuração de um modo."""
    return MODE_CONFIGS.get(mode, MODE_CONFIGS[BotMode.NORMAL])


def list_modes() -> List[dict]:
    """Lista todos os modos disponíveis."""
    return [
        {
            "id": mode.value,
            "name": config.name,
            "description": config.description,
            "icon": config.icon,
            "editable": config.editable
        }
        for mode, config in MODE_CONFIGS.items()
    ]
