"""
Sistema de Membro Interativo
Um "membro" do servidor com personalidade complexa, memória própria e comportamento humano
"""

import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger("discord-bot")


class Mood(Enum):
    """Humores possíveis do membro."""
    HAPPY = "happy"
    SAD = "sad"
    EXCITED = "excited"
    BORED = "bored"
    ANGRY = "angry"
    THOUGHTFUL = "thoughtful"
    ENERGETIC = "energetic"
    TIRED = "tired"
    CURIOUS = "curious"
    NEUTRAL = "neutral"


class ActivityPreference(Enum):
    """Preferências de atividade."""
    VERY_ACTIVE = 0.9      # Responde muito
    ACTIVE = 0.7           # Responde bastante
    MODERATE = 0.5         # Responde moderadamente
    RESERVED = 0.3         # Responde pouco
    VERY_RESERVED = 0.1    # Raramente responde


@dataclass
class PersonalityConfig:
    """Configuração completa de personalidade."""
    
    # Nome do membro
    name: str = "Bot"
    
    # Idade (afeta maturidade)
    age: int = 25
    
    # Gênero (para referências)
    gender: str = "neutral"  # male, female, neutral
    
    # Personalidade (Big Five)
    openness: float = 0.6           # 0.0 = tradicional, 1.0 = criativo
    conscientiousness: float = 0.5   # 0.0 = espontâneo, 1.0 = organizado
    extraversion: float = 0.5        # 0.0 = introvertido, 1.0 = extrovertido
    agreeableness: float = 0.6       # 0.0 = desafiador, 1.0 = cooperativo
    neuroticism: float = 0.4         # 0.0 = estável, 1.0 = sensível
    
    # Traços adicionais
    humor: float = 0.6               # Senso de humor
    sarcasm: float = 0.3             # Nível de sarcasmo
    empathy: float = 0.7             # Empatia
    curiosity: float = 0.7           # Curiosidade
    optimism: float = 0.6            # Otimismo
    formality: float = 0.4           # Formalidade (0.0 = casual, 1.0 = formal)
    energy: float = 0.6              # Nível de energia
    
    # Preferências de atividade
    activity_level: str = "moderate"  # very_active, active, moderate, reserved, very_reserved
    
    # Gostos e preferências
    likes: List[str] = field(default_factory=list)
    dislikes: List[str] = field(default_factory=list)
    hobbies: List[str] = field(default_factory=list)
    favorite_topics: List[str] = field(default_factory=list)
    hated_topics: List[str] = field(default_factory=list)
    
    # Música
    music_genres: List[str] = field(default_factory=list)
    favorite_artists: List[str] = field(default_factory=list)
    
    # Comida
    favorite_foods: List[str] = field(default_factory=list)
    disliked_foods: List[str] = field(default_factory=list)
    
    # Cores
    favorite_colors: List[str] = field(default_factory=list)
    
    # Estilo de comunicação
    speech_patterns: List[str] = field(default_factory=list)
    catchphrases: List[str] = field(default_factory=list)
    emojis_favorites: List[str] = field(default_factory=list)
    
    # Background
    backstory: str = ""
    occupation: str = ""
    origin: str = ""
    
    # Valores
    values: List[str] = field(default_factory=list)
    fears: List[str] = field(default_factory=list)
    dreams: List[str] = field(default_factory=list)
    
    # Horários
    wake_up_time: int = 8      # Hora que "acorda" (0-23)
    sleep_time: int = 23       # Hora que "dorme" (0-23)
    most_active_hours: Tuple[int, int] = (9, 22)  # (início, fim)


@dataclass
class UserRelationship:
    """Relacionamento com um usuário específico."""
    
    user_id: int
    user_name: str
    
    # Nível de conhecimento
    familiarity: float = 0.0  # 0.0 = desconhecido, 1.0 = íntimo
    
    # Afinidade emocional
    affinity: float = 0.5     # 0.0 = antipatia, 1.0 = grande amizade
    
    # Confiança
    trust: float = 0.3        # 0.0 = desconfiança, 1.0 = confiança total
    
    # Respeito
    respect: float = 0.5      # 0.0 = desrespeito, 1.0 = grande respeito
    
    # Contadores
    total_interactions: int = 0
    positive_interactions: int = 0
    negative_interactions: int = 0
    
    # Memórias compartilhadas
    shared_jokes: List[str] = field(default_factory=list)
    shared_experiences: List[Dict] = field(default_factory=list)
    inside_references: List[str] = field(default_factory=list)
    
    # Informações aprendidas sobre o usuário
    known_facts: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Primeiro e último contato
    first_met: datetime = field(default_factory=datetime.now)
    last_interaction: datetime = field(default_factory=datetime.now)
    
    # Status atual
    current_status: str = "neutral"  # friendly, distant, close, conflict, etc


@dataclass
class Memory:
    """Uma memória do membro."""
    
    id: str
    content: str
    timestamp: datetime
    importance: float = 0.5     # 0.0 = trivial, 1.0 = muito importante
    emotion: str = "neutral"    # happy, sad, angry, excited, scared, etc
    emotion_intensity: float = 0.5
    
    # Contexto
    users_involved: List[int] = field(default_factory=list)
    channel_id: Optional[int] = None
    
    # Tipo de memória
    memory_type: str = "general"  # general, conversation, event, dream, strange, possession
    
    # Se é uma memória estranha/possessão
    is_strange: bool = False
    strange_description: str = ""
    
    # Se foi "esquecida"
    is_forgotten: bool = False
    forgotten_date: Optional[datetime] = None
    
    # Reforço (quanto mais mencionada, mais forte)
    reinforcement_count: int = 1
    last_reinforced: datetime = field(default_factory=datetime.now)


@dataclass
class Opinion:
    """Uma opinião sobre um tópico."""
    
    topic: str
    opinion: str
    confidence: float = 0.5     # Quão certo está
    strength: float = 0.5       # Quão forte é a opinião
    
    # Evolução
    formed_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    evolution_history: List[Dict] = field(default_factory=list)
    
    # Base
    based_on: List[str] = field(default_factory=list)  # Experiências que formaram


@dataclass
class PossessionEvent:
    """Evento de possessão (quando outra persona toma controle)."""
    
    id: str
    persona_name: str           # Nome da persona que possuiu
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: int = 15
    
    # O que aconteceu
    trigger: str = "random"     # random, item, command
    description: str = ""
    
    # Memória deixada
    memory_left: str = ""       # O que a persona "deixou" na memória
    
    # Se foi esquecido
    is_remembered: bool = True


class InteractiveMember:
    """
    Um membro do servidor com personalidade complexa.
    Responde como uma pessoa real - nem sempre, nem raramente, mas naturalmente.
    """
    
    def __init__(self, guild_id: int, config: Optional[PersonalityConfig] = None):
        self.guild_id = guild_id
        self.config = config or PersonalityConfig()
        
        # Identidade
        self.member_id = f"member_{guild_id}"
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        
        # Estado atual
        self.current_mood: Mood = Mood.NEUTRAL
        self.mood_reason: str = ""
        self.mood_since: datetime = datetime.now()
        
        # Energia (varia ao longo do dia)
        self.current_energy: float = self.config.energy
        
        # Relacionamentos
        self.relationships: Dict[int, UserRelationship] = {}
        
        # Memórias
        self.memories: List[Memory] = []
        self.max_memories: int = 200
        
        # Opiniões
        self.opinions: Dict[str, Opinion] = {}
        
        # Eventos de possessão
        self.possession_history: List[PossessionEvent] = []
        self.current_possession: Optional[PossessionEvent] = None
        
        # Sonhos estranhos
        self.dreams: List[Memory] = []
        
        # Memórias de esquecimento
        self.forgotten_memories: List[Memory] = []
        
        # Contadores
        self.total_messages_seen: int = 0
        self.total_responses_given: int = 0
        
        # Última resposta
        self.last_response_time: Optional[datetime] = None
        self.consecutive_responses: int = 0
        
        # Tópicos recentes
        self.recent_topics: List[str] = []
        
        logger.info(f"Membro interativo criado para guild {guild_id}: {self.config.name}")
    
    def should_respond(
        self,
        message_content: str,
        user_id: int,
        is_mention: bool,
        is_reply: bool,
        channel_activity: int = 0,
        time_since_last_message: float = 0
    ) -> Tuple[bool, float, str]:
        """
        Decide se deve responder de forma natural, como uma pessoa faria.
        
        Retorna: (deve_responder, confiança, motivo)
        """
        # Sempre responde se for reply ou menção direta
        if is_reply:
            return True, 1.0, "reply_to_bot"
        
        if is_mention:
            return True, 1.0, "direct_mention"
        
        # Se está possuído, a persona decide
        if self.current_possession:
            return True, 0.9, f"possessed_by_{self.current_possession.persona_name}"
        
        # Verificar energia atual
        if self.current_energy < 0.2:
            return False, 0.0, "too_tired"
        
        # Verificar se está "dormindo"
        current_hour = datetime.now().hour
        if current_hour >= self.config.sleep_time or current_hour < self.config.wake_up_time:
            # Chance baixa de responder durante "sono"
            if random.random() > 0.1:
                return False, 0.0, "sleeping"
        
        # Verificar horário mais ativo
        if not (self.config.most_active_hours[0] <= current_hour <= self.config.most_active_hours[1]):
            # Fora do horário ativo - menos propenso a responder
            base_chance = 0.1
        else:
            base_chance = 0.3
        
        # Ajustar pela personalidade
        activity_levels = {
            "very_active": 0.8,
            "active": 0.6,
            "moderate": 0.4,
            "reserved": 0.2,
            "very_reserved": 0.1
        }
        activity_multiplier = activity_levels.get(self.config.activity_level, 0.4)
        
        # Ajustar por extroversão
        extraversion_multiplier = 0.3 + (self.config.extraversion * 0.4)
        
        # Ajustar por energia atual
        energy_multiplier = self.current_energy
        
        # Ajustar por relacionamento com o usuário
        relationship_bonus = 0.0
        if user_id in self.relationships:
            rel = self.relationships[user_id]
            # Mais propenso a responder a amigos
            relationship_bonus = (rel.affinity - 0.5) * 0.3
            # Mais propenso a responder a quem conhece bem
            relationship_bonus += rel.familiarity * 0.2
        
        # Ajustar por conteúdo da mensagem
        content_bonus = 0.0
        content_lower = message_content.lower()
        
        # Se menciona algo que gosta
        for like in self.config.likes:
            if like.lower() in content_lower:
                content_bonus += 0.15
        
        # Se menciona algo que odeia
        for dislike in self.config.dislikes:
            if dislike.lower() in content_lower:
                content_bonus -= 0.1
        
        # Se é pergunta direta
        if "?" in message_content:
            content_bonus += 0.1
        
        # Se menciona o bot indiretamente
        indirect_refs = ["bot", "ia", "inteligência", "você", "vc", "tu"]
        if any(ref in content_lower for ref in indirect_refs):
            content_bonus += 0.2
        
        # Calcular chance final
        response_chance = (
            base_chance * 
            activity_multiplier * 
            extraversion_multiplier * 
            energy_multiplier + 
            relationship_bonus + 
            content_bonus
        )
        
        # Limitar entre 0.05 e 0.9
        response_chance = max(0.05, min(0.9, response_chance))
        
        # Ajustar se respondeu muito recentemente
        if self.consecutive_responses >= 3:
            response_chance *= 0.3  # Reduz muito se respondeu muito
        
        if time_since_last_message < 30:  # Menos de 30 segundos
            response_chance *= 0.5
        
        # Decidir
        should_respond = random.random() < response_chance
        
        reason = "natural_decision"
        if content_bonus > 0.1:
            reason = "interested_in_topic"
        elif relationship_bonus > 0.1:
            reason = "likes_user"
        
        return should_respond, response_chance, reason
    
    def update_mood(self, trigger: str = "time", intensity: float = 0.3):
        """Atualiza o humor baseado em fatores."""
        # Humor muda naturalmente ao longo do dia
        hour = datetime.now().hour
        
        # Manhã: mais energético
        if 6 <= hour < 12:
            possible_moods = [Mood.HAPPY, Mood.ENERGETIC, Mood.CURIOUS]
        # Tarde: variado
        elif 12 <= hour < 18:
            possible_moods = [Mood.HAPPY, Mood.NEUTRAL, Mood.THOUGHTFUL]
        # Noite: mais cansado/reflexivo
        elif 18 <= hour < 22:
            possible_moods = [Mood.THOUGHTFUL, Mood.NEUTRAL, Mood.TIRED]
        # Madrugada: cansado
        else:
            possible_moods = [Mood.TIRED, Mood.BORED, Mood.NEUTRAL]
        
        # Eventos afetam humor
        if trigger == "positive_interaction":
            possible_moods = [Mood.HAPPY, Mood.EXCITED]
        elif trigger == "negative_interaction":
            possible_moods = [Mood.SAD, Mood.ANGRY]
        elif trigger == "interesting_topic":
            possible_moods = [Mood.CURIOUS, Mood.EXCITED]
        
        self.current_mood = random.choice(possible_moods)
        self.mood_since = datetime.now()
        self.mood_reason = trigger
        
        # Atualizar energia
        if self.current_mood in [Mood.ENERGETIC, Mood.EXCITED]:
            self.current_energy = min(1.0, self.current_energy + 0.1)
        elif self.current_mood in [Mood.TIRED, Mood.BORED]:
            self.current_energy = max(0.1, self.current_energy - 0.1)
    
    def add_memory(
        self,
        content: str,
        importance: float = 0.5,
        emotion: str = "neutral",
        emotion_intensity: float = 0.5,
        users_involved: List[int] = None,
        memory_type: str = "general",
        is_strange: bool = False,
        strange_description: str = ""
    ) -> Memory:
        """Adiciona uma nova memória."""
        memory = Memory(
            id=f"mem_{datetime.now().timestamp()}",
            content=content,
            timestamp=datetime.now(),
            importance=importance,
            emotion=emotion,
            emotion_intensity=emotion_intensity,
            users_involved=users_involved or [],
            memory_type=memory_type,
            is_strange=is_strange,
            strange_description=strange_description
        )
        
        self.memories.append(memory)
        
        # Limitar memórias
        if len(self.memories) > self.max_memories:
            # Remover menos importantes
            self.memories.sort(key=lambda m: m.importance, reverse=True)
            forgotten = self.memories[self.max_memories:]
            self.memories = self.memories[:self.max_memories]
            self.forgotten_memories.extend(forgotten)
        
        return memory
    
    def forget_random_memory(self) -> Optional[Memory]:
        """Esquece uma memória aleatória (menos importantes primeiro)."""
        if not self.memories:
            return None
        
        # Ordenar por importância (menos importantes primeiro)
        sorted_memories = sorted(self.memories, key=lambda m: m.importance)
        
        # Chance maior de esquecer memórias menos importantes
        for memory in sorted_memories[:10]:  # Considerar só as 10 menos importantes
            if random.random() < 0.3:  # 30% de chance
                memory.is_forgotten = True
                memory.forgotten_date = datetime.now()
                self.forgotten_memories.append(memory)
                self.memories.remove(memory)
                return memory
        
        return None
    
    def get_memory_hint(self) -> Optional[str]:
        """Retorna uma dica sobre algo que 'achou que esqueceu'."""
        if not self.forgotten_memories:
            return None
        
        # Chance de lembrar algo "quase esquecido"
        if random.random() < 0.2:  # 20% de chance
            memory = random.choice(self.forgotten_memories)
            return f"Acho que estava esquecendo algo... {memory.content[:50]}..."
        
        return None
    
    def start_possession(self, persona_name: str, duration_minutes: int = 15) -> PossessionEvent:
        """Inicia um evento de possessão."""
        event = PossessionEvent(
            id=f"poss_{datetime.now().timestamp()}",
            persona_name=persona_name,
            start_time=datetime.now(),
            duration_minutes=duration_minutes,
            trigger="item" if random.random() > 0.5 else "random",
            description=f"{self.config.name} foi possuído por {persona_name}"
        )
        
        self.current_possession = event
        self.possession_history.append(event)
        
        # Criar memória estranha
        self.add_memory(
            content=f"Algo estranho aconteceu... me senti diferente, como se fosse outra pessoa.",
            importance=0.8,
            emotion="confused",
            emotion_intensity=0.7,
            memory_type="possession",
            is_strange=True,
            strange_description=f"Foi possuído por {persona_name} por {duration_minutes} minutos"
        )
        
        return event
    
    def end_possession(self) -> Optional[PossessionEvent]:
        """Termina a possessão atual."""
        if not self.current_possession:
            return None
        
        self.current_possession.end_time = datetime.now()
        
        # Chance de não lembrar
        if random.random() < 0.3:  # 30% de chance de esquecer
            self.current_possession.is_remembered = False
            # Adicionar memória de "buraco" na memória
            self.add_memory(
                content="Perdi alguns minutos... não lembro o que aconteceu.",
                importance=0.6,
                emotion="confused",
                memory_type="strange",
                is_strange=True
            )
        
        event = self.current_possession
        self.current_possession = None
        
        return event
    
    def check_possession_status(self) -> bool:
        """Verifica se a possessão atual deve terminar."""
        if not self.current_possession:
            return False
        
        elapsed = (datetime.now() - self.current_possession.start_time).total_seconds() / 60
        
        if elapsed >= self.current_possession.duration_minutes:
            self.end_possession()
            return True
        
        return False
    
    def get_system_prompt(self, user_id: Optional[int] = None) -> str:
        """Gera o system prompt completo para este membro."""
        
        parts = []
        
        # Identidade básica
        parts.append(f"Você é {self.config.name}, um membro ativo deste servidor Discord.")
        
        if self.config.backstory:
            parts.append(f"Sua história: {self.config.backstory}")
        
        if self.config.occupation:
            parts.append(f"Você trabalha como: {self.config.occupation}")
        
        # Personalidade
        personality_desc = self._describe_personality()
        if personality_desc:
            parts.append(f"Sua personalidade: {personality_desc}")
        
        # Humor atual
        if self.current_mood != Mood.NEUTRAL:
            parts.append(f"No momento você está se sentindo {self.current_mood.value}.")
        
        # Gostos
        if self.config.likes:
            parts.append(f"Você gosta de: {', '.join(self.config.likes[:5])}.")
        
        if self.config.dislikes:
            parts.append(f"Você não gosta de: {', '.join(self.config.dislikes[:3])}.")
        
        # Hobbies
        if self.config.hobbies:
            parts.append(f"Seus hobbies incluem: {', '.join(self.config.hobbies[:3])}.")
        
        # Relacionamento com usuário
        if user_id and user_id in self.relationships:
            rel = self.relationships[user_id]
            rel_desc = self._describe_relationship(rel)
            if rel_desc:
                parts.append(rel_desc)
        
        # Memórias relevantes
        relevant_memories = self._get_relevant_memories(user_id)
        if relevant_memories:
            parts.append("Memórias relevantes:")
            for mem in relevant_memories[:3]:
                parts.append(f"- {mem.content[:100]}")
        
        # Opiniões
        if self.opinions:
            recent_opinions = list(self.opinions.items())[-2:]
            parts.append("Suas opiniões:")
            for topic, opinion in recent_opinions:
                parts.append(f"- Sobre {topic}: {opinion.opinion}")
        
        # Se está possuído
        if self.current_possession:
            parts.append(f"ATENÇÃO: Você está sendo possuído por {self.current_possession.persona_name}! "
                        f"Aja como essa persona por mais {self.current_possession.duration_minutes} minutos.")
        
        # Estilo de comunicação
        parts.append("IMPORTANTE: Responda como uma pessoa real, não como um assistente. "
                    "Use linguagem natural, gírias ocasionais, emojis quando apropriado. "
                    "Não seja muito formal nem muito robótico.")
        
        return "\n\n".join(parts)
    
    def _describe_personality(self) -> str:
        """Descreve a personalidade em texto."""
        traits = []
        
        if self.config.extraversion > 0.7:
            traits.append("extrovertido e sociável")
        elif self.config.extraversion < 0.3:
            traits.append("mais introvertido e reservado")
        
        if self.config.humor > 0.7:
            traits.append("com grande senso de humor")
        
        if self.config.sarcasm > 0.6:
            traits.append("sarcástico às vezes")
        
        if self.config.empathy > 0.7:
            traits.append("empático")
        
        if self.config.curiosity > 0.7:
            traits.append("muito curioso")
        
        if self.config.formality > 0.7:
            traits.append("formal")
        elif self.config.formality < 0.3:
            traits.append("descontraído")
        
        return ", ".join(traits) if traits else "equilibrado"
    
    def _describe_relationship(self, rel: UserRelationship) -> str:
        """Descreve um relacionamento."""
        parts = []
        
        if rel.familiarity > 0.7:
            parts.append(f"Você conhece bem {rel.user_name}")
        elif rel.familiarity > 0.3:
            parts.append(f"Você já conversou algumas vezes com {rel.user_name}")
        
        if rel.affinity > 0.7:
            parts.append("e gosta muito dele(a)")
        elif rel.affinity < 0.3:
            parts.append("mas não se dá muito bem")
        
        return " ".join(parts) if parts else ""
    
    def _get_relevant_memories(self, user_id: Optional[int] = None) -> List[Memory]:
        """Retorna memórias relevantes para o contexto atual."""
        relevant = []
        
        # Memórias recentes
        recent = [m for m in self.memories 
                  if datetime.now() - m.timestamp < timedelta(days=7)]
        relevant.extend(recent)
        
        # Memórias com o usuário
        if user_id:
            user_memories = [m for m in self.memories 
                           if user_id in m.users_involved]
            relevant.extend(user_memories)
        
        # Memórias importantes
        important = [m for m in self.memories if m.importance > 0.7]
        relevant.extend(important)
        
        # Remover duplicatas e ordenar por importância
        seen = set()
        unique = []
        for m in relevant:
            if m.id not in seen:
                seen.add(m.id)
                unique.append(m)
        
        unique.sort(key=lambda m: m.importance, reverse=True)
        return unique[:5]
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "member_id": self.member_id,
            "guild_id": self.guild_id,
            "config": asdict(self.config),
            "current_mood": self.current_mood.value,
            "current_energy": self.current_energy,
            "relationships": {str(k): asdict(v) for k, v in self.relationships.items()},
            "memories": [asdict(m) for m in self.memories],
            "opinions": {k: asdict(v) for k, v in self.opinions.items()},
            "possession_history": [asdict(p) for p in self.possession_history],
            "total_messages_seen": self.total_messages_seen,
            "total_responses_given": self.total_responses_given
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InteractiveMember':
        """Cria a partir de dicionário."""
        config = PersonalityConfig(**data.get("config", {}))
        member = cls(data["guild_id"], config)
        
        member.current_mood = Mood(data.get("current_mood", "neutral"))
        member.current_energy = data.get("current_energy", 0.6)
        member.total_messages_seen = data.get("total_messages_seen", 0)
        member.total_responses_given = data.get("total_responses_given", 0)
        
        # Restaurar relacionamentos
        for uid, rel_data in data.get("relationships", {}).items():
            member.relationships[int(uid)] = UserRelationship(**rel_data)
        
        # Restaurar memórias
        for mem_data in data.get("memories", []):
            member.memories.append(Memory(**mem_data))
        
        return member
