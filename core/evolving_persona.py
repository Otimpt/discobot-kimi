"""
Sistema de Personas Evolutivas
Personas que aprendem, adaptam e evoluem com o tempo
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger("discord-bot")


@dataclass
class PersonalityTraits:
    """Traços de personalidade que podem evoluir."""
    
    # Big Five + extras
    openness: float = 0.5           # Abertura a novas experiências
    conscientiousness: float = 0.5  # Conscienciosidade
    extraversion: float = 0.5       # Extroversão
    agreeableness: float = 0.5      # Amabilidade
    neuroticism: float = 0.5        # Neuroticismo
    
    # Traços adicionais
    humor: float = 0.5              # Senso de humor
    sarcasm: float = 0.3            # Sarcasmo
    empathy: float = 0.6            # Empatia
    curiosity: float = 0.7          # Curiosidade
    formality: float = 0.4          # Formalidade


@dataclass
class Preferences:
    """Preferências da persona."""
    
    topics_liked: List[str] = None
    topics_disliked: List[str] = None
    music_genres: List[str] = None
    hobbies: List[str] = None
    foods: List[str] = None
    colors: List[str] = None
    
    def __post_init__(self):
        if self.topics_liked is None:
            self.topics_liked = []
        if self.topics_disliked is None:
            self.topics_disliked = []
        if self.music_genres is None:
            self.music_genres = []
        if self.hobbies is None:
            self.hobbies = []
        if self.foods is None:
            self.foods = []
        if self.colors is None:
            self.colors = []


@dataclass
class EmotionalMemory:
    """Memórias emocionais sobre eventos/pessoas."""
    
    user_id: int
    event_description: str
    emotion: str  # happy, sad, angry, excited, bored, etc
    intensity: float  # 0.0 a 1.0
    timestamp: datetime
    context: str = ""


@dataclass
class Relationship:
    """Relacionamento com um usuário."""
    
    user_id: int
    user_name: str
    familiarity: float = 0.0  # 0.0 a 1.0 - quão bem conhece
    affinity: float = 0.5     # 0.0 a 1.0 - quão gosta
    interactions_count: int = 0
    first_met: datetime = None
    last_interaction: datetime = None
    shared_jokes: List[str] = None
    user_preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.first_met is None:
            self.first_met = datetime.now()
        if self.shared_jokes is None:
            self.shared_jokes = []
        if self.user_preferences is None:
            self.user_preferences = {}


class EvolvingPersona:
    """Uma persona que evolui com o tempo."""
    
    def __init__(self, persona_id: str, name: str, base_prompt: str):
        self.persona_id = persona_id
        self.name = name
        self.base_prompt = base_prompt
        
        # Data de criação
        self.created_at = datetime.now()
        self.last_evolution = datetime.now()
        
        # Traços de personalidade (evoluem lentamente)
        self.traits = PersonalityTraits()
        
        # Preferências (aprendidas com o tempo)
        self.preferences = Preferences()
        
        # Memórias emocionais
        self.emotional_memories: List[EmotionalMemory] = []
        
        # Relacionamentos com usuários
        self.relationships: Dict[int, Relationship] = {}
        
        # Fatos aprendidos sobre o mundo/servidor
        self.learned_facts: List[Dict[str, Any]] = []
        
        # Histórico de evolução
        self.evolution_history: List[Dict[str, Any]] = []
        
        # Opiniões formadas
        self.opinions: Dict[str, str] = {}
        
        # Frases/características de fala desenvolvidas
        self.speech_patterns: List[str] = []
        
        # Humor atual (muda ao longo do dia)
        self.current_mood = "neutral"
        self.mood_factors: Dict[str, float] = {}
    
    def interact_with_user(self, user_id: int, user_name: str, 
                          message_content: str, sentiment: str = "neutral"):
        """Registra uma interação com um usuário."""
        
        # Atualizar ou criar relacionamento
        if user_id not in self.relationships:
            self.relationships[user_id] = Relationship(
                user_id=user_id,
                user_name=user_name
            )
        
        rel = self.relationships[user_id]
        rel.interactions_count += 1
        rel.last_interaction = datetime.now()
        
        # Aumentar familiaridade
        rel.familiarity = min(1.0, rel.familiarity + 0.02)
        
        # Ajustar afinidade baseado no sentimento
        if sentiment == "positive":
            rel.affinity = min(1.0, rel.affinity + 0.05)
        elif sentiment == "negative":
            rel.affinity = max(0.0, rel.affinity - 0.03)
        
        # Registrar memória emocional se sentimento forte
        if sentiment in ["very_positive", "very_negative", "angry", "excited"]:
            self.add_emotional_memory(
                user_id=user_id,
                event_description=f"Interação com {user_name}: {message_content[:100]}",
                emotion=sentiment,
                intensity=0.7
            )
    
    def add_emotional_memory(self, user_id: int, event_description: str, 
                            emotion: str, intensity: float, context: str = ""):
        """Adiciona uma memória emocional."""
        memory = EmotionalMemory(
            user_id=user_id,
            event_description=event_description,
            emotion=emotion,
            intensity=intensity,
            timestamp=datetime.now(),
            context=context
        )
        self.emotional_memories.append(memory)
        
        # Limitar memórias (manter últimas 100)
        if len(self.emotional_memories) > 100:
            self.emotional_memories = self.emotional_memories[-100:]
    
    def learn_fact(self, fact: str, source: str = "conversation", 
                   importance: float = 0.5):
        """Aprende um novo fato."""
        self.learned_facts.append({
            "fact": fact,
            "source": source,
            "importance": importance,
            "learned_at": datetime.now(),
            "reinforced_count": 1
        })
    
    def form_opinion(self, topic: str, opinion: str, confidence: float = 0.5):
        """Forma uma opinião sobre um tópico."""
        self.opinions[topic] = {
            "opinion": opinion,
            "confidence": confidence,
            "formed_at": datetime.now()
        }
    
    def evolve_traits(self):
        """Evolui os traços de personalidade baseado nas experiências."""
        
        # Analisar memórias emocionais recentes
        recent_memories = [
            m for m in self.emotional_memories 
            if datetime.now() - m.timestamp < timedelta(days=7)
        ]
        
        if not recent_memories:
            return
        
        # Ajustar traços baseado nas memórias
        positive_count = sum(1 for m in recent_memories 
                           if m.emotion in ["happy", "excited", "very_positive"])
        negative_count = sum(1 for m in recent_memories 
                           if m.emotion in ["sad", "angry", "very_negative"])
        
        total = len(recent_memories)
        if total > 0:
            # Mais experiências positivas = mais extrovertido
            if positive_count / total > 0.6:
                self.traits.extraversion = min(1.0, self.traits.extraversion + 0.01)
            
            # Mais experiências negativas = mais neuroticismo
            if negative_count / total > 0.4:
                self.traits.neuroticism = min(1.0, self.traits.neuroticism + 0.01)
        
        self.last_evolution = datetime.now()
        
        # Registrar evolução
        self.evolution_history.append({
            "timestamp": datetime.now(),
            "traits": asdict(self.traits),
            "trigger": "memory_analysis"
        })
    
    def get_relationship_context(self, user_id: int) -> str:
        """Gera contexto sobre o relacionamento com um usuário."""
        if user_id not in self.relationships:
            return "Não conheço bem esta pessoa ainda."
        
        rel = self.relationships[user_id]
        
        context_parts = []
        
        # Familiaridade
        if rel.familiarity < 0.2:
            context_parts.append(f"Estou conhecendo {rel.user_name}.")
        elif rel.familiarity < 0.5:
            context_parts.append(f"Já conversei algumas vezes com {rel.user_name}.")
        elif rel.familiarity < 0.8:
            context_parts.append(f"Conheço bem {rel.user_name}.")
        else:
            context_parts.append(f"{rel.user_name} é alguém que considero próximo!")
        
        # Afinidade
        if rel.affinity > 0.7:
            context_parts.append("Gosto muito de conversar com esta pessoa.")
        elif rel.affinity < 0.3:
            context_parts.append("Nossas interações têm sido um pouco tensas.")
        
        # Memórias compartilhadas
        if rel.shared_jokes:
            context_parts.append(f"Temos piadas internas: {', '.join(rel.shared_jokes[:2])}")
        
        return " ".join(context_parts)
    
    def get_system_prompt(self, user_id: Optional[int] = None) -> str:
        """Gera o system prompt completo para esta persona."""
        
        prompt_parts = [self.base_prompt]
        
        # Adicionar traços de personalidade
        traits_desc = self._describe_traits()
        if traits_desc:
            prompt_parts.append(f"\nSua personalidade: {traits_desc}")
        
        # Adicionar preferências
        if self.preferences.topics_liked:
            prompt_parts.append(f"\nVocê gosta de: {', '.join(self.preferences.topics_liked[:5])}")
        
        if self.preferences.hobbies:
            prompt_parts.append(f"\nSeus hobbies incluem: {', '.join(self.preferences.hobbies[:3])}")
        
        # Adicionar contexto de relacionamento se usuário especificado
        if user_id:
            rel_context = self.get_relationship_context(user_id)
            prompt_parts.append(f"\n{rel_context}")
        
        # Adicionar opiniões relevantes
        if self.opinions:
            recent_opinions = list(self.opinions.items())[-3:]
            opinions_text = " | ".join([f"{k}: {v['opinion']}" for k, v in recent_opinions])
            prompt_parts.append(f"\nSuas opiniões: {opinions_text}")
        
        # Adicionar humor atual
        if self.current_mood != "neutral":
            prompt_parts.append(f"\nVocê está se sentindo {self.current_mood} hoje.")
        
        return "\n".join(prompt_parts)
    
    def _describe_traits(self) -> str:
        """Descreve os traços de personalidade em texto."""
        descriptions = []
        
        if self.traits.extraversion > 0.7:
            descriptions.append("extrovertido e energético")
        elif self.traits.extraversion < 0.3:
            descriptions.append("mais reservado e introvertido")
        
        if self.traits.humor > 0.7:
            descriptions.append("com grande senso de humor")
        
        if self.traits.sarcasm > 0.6:
            descriptions.append("sarcástico às vezes")
        
        if self.traits.empathy > 0.7:
            descriptions.append("empático e compreensivo")
        
        if self.traits.curiosity > 0.7:
            descriptions.append("muito curioso")
        
        if self.traits.formality > 0.7:
            descriptions.append("formal")
        elif self.traits.formality < 0.3:
            descriptions.append("descontraído")
        
        return ", ".join(descriptions) if descriptions else ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "persona_id": self.persona_id,
            "name": self.name,
            "base_prompt": self.base_prompt,
            "created_at": self.created_at.isoformat(),
            "last_evolution": self.last_evolution.isoformat(),
            "traits": asdict(self.traits),
            "preferences": asdict(self.preferences),
            "emotional_memories": [
                {**asdict(m), "timestamp": m.timestamp.isoformat()}
                for m in self.emotional_memories
            ],
            "relationships": {
                str(k): {
                    **{key: val for key, val in asdict(v).items() if key not in ['first_met', 'last_interaction']},
                    "first_met": v.first_met.isoformat() if v.first_met else None,
                    "last_interaction": v.last_interaction.isoformat() if v.last_interaction else None
                }
                for k, v in self.relationships.items()
            },
            "learned_facts": self.learned_facts,
            "opinions": self.opinions,
            "current_mood": self.current_mood
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvolvingPersona':
        """Cria a partir de dicionário."""
        persona = cls(
            persona_id=data["persona_id"],
            name=data["name"],
            base_prompt=data["base_prompt"]
        )
        
        # Restaurar traços
        if "traits" in data:
            persona.traits = PersonalityTraits(**data["traits"])
        
        # Restaurar preferências
        if "preferences" in data:
            persona.preferences = Preferences(**data["preferences"])
        
        # Restaurar relacionamentos
        if "relationships" in data:
            for uid, rel_data in data["relationships"].items():
                rel = Relationship(
                    user_id=int(uid),
                    user_name=rel_data["user_name"],
                    familiarity=rel_data.get("familiarity", 0.0),
                    affinity=rel_data.get("affinity", 0.5),
                    interactions_count=rel_data.get("interactions_count", 0)
                )
                persona.relationships[int(uid)] = rel
        
        # Restaurar opiniões
        if "opinions" in data:
            persona.opinions = data["opinions"]
        
        # Restaurar humor
        if "current_mood" in data:
            persona.current_mood = data["current_mood"]
        
        return persona
