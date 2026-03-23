# 📚 Documentação Completa - Discord AI Bot v2

## 🎯 Visão Geral

Este é um bot de Discord avançado com múltiplos modos de operação, sistema de personas evolutivas, suporte a diversos provedores de LLM e muitas funcionalidades inteligentes.

---

## 🎮 Modos de Operação

O bot possui **5 modos de operação** distintos:

### 1. 💬 Modo Normal
**Descrição**: Chat completion padrão com histórico de conversas.

**Características**:
- Usa API de chat completion (OpenAI, Anthropic, etc)
- Mantém histórico de mensagens
- Responde aos gatilhos configurados
- Suporta ferramentas (tools)

**Quando usar**: Para conversas normais, perguntas e respostas.

**Gatilhos configuráveis**:
- Reply (sempre ativo)
- Menção (@Bot)
- Prefixo (!comando)
- Interrogação (?)
- Ambos (prefixo OU menção)

---

### 2. 🤖 Modo Assistant
**Descrição**: OpenAI Assistant API com ferramentas avançadas.

**Características**:
- Acesso a ferramentas: code_interpreter, file_search, functions
- Threads persistentes
- Pode executar código Python
- Buscar em arquivos
- Usar funções customizadas

**Quando usar**: Para tarefas complexas que precisam de ferramentas.

**Configuração**:
```yaml
assistant:
  id: "asst_xxxxxxxx"  # ID do Assistant na OpenAI
  tools:
    code_interpreter: true
    file_search: true
    functions:
      - google_search
```

**Comando para ativar**:
```
/modo assistant
# ou
/config contexto assistant
/config assistente <id>
```

---

### 3. 🎯 Modo Chatbot
**Descrição**: Responde automaticamente sem precisar de gatilhos.

**Características**:
- IA decide quando responder
- Não precisa de menção, reply ou prefixo
- Sensibilidade configurável (low/normal/high)
- Participa ativamente das conversas

**Quando usar**: Quando quer que o bot participe naturalmente das conversas.

**Como funciona**:
- Sensibilidade **Low**: Responde pouco, só quando mencionado indiretamente
- Sensibilidade **Normal**: Responde a perguntas e quando o contexto pede
- Sensibilidade **High**: Participa frequentemente

**Comando para ativar**:
```
/modo chatbot
/config modo chatbot
```

---

### 4. 👤 Modo Interativo
**Descrição**: Membro do servidor com personalidade complexa e memória.

**Características**:
- Tem personalidade única que evolui
- Desenvolve relacionamentos com usuários
- Forma opiniões ao longo do tempo
- Tem memórias emocionais
- Lembra de conversas passadas
- Tem gostos, hobbies, preferências

**Quando usar**: Quando quer um "membro" do servidor, não apenas um assistente.

**Como funciona**:
```
1. Cria uma persona evolutiva
2. Ela começa com uma base de personalidade
3. A cada interação, ela aprende sobre as pessoas
4. Desenvolve relacionamentos (familiaridade, afinidade)
5. Forma opiniões sobre tópicos
6. Evolui traços de personalidade
7. Tem memórias emocionais de eventos importantes
```

**Traços que evoluem**:
- Extroversão/Introversão
- Senso de humor
- Empatia
- Curiosidade
- Formalidade
- Sarcasmo

**Comando para ativar**:
```
/modo interativo
/persona evolutiva criar
```

---

### 5. 🎭 Modo Roleplay
**Descrição**: Persona específica com comportamento definido.

**Características**:
- Usa uma persona predefinida
- Mantém consistência de personagem
- Pode ser persona global ou do servidor
- Pode usar Prompt ID da OpenAI

**Quando usar**: Para interpretar personagens específicos.

**Exemplos de personas**:
- Professor de Python
- Pirata do século XVIII
- Cientista louco
- Assistente formal
- Amigo descontraído

**Comando para ativar**:
```
/persona usar <nome>
/modo roleplay
```

---

## 🔔 Sistema de Gatilhos

### Reply (SEMPRE ATIVO)
```
Reply às mensagens do bot → SEMPRE responde
```
Este gatilho **não pode ser desativado**.

### Outros Gatilhos (configuráveis)

| Gatilho | Descrição | Comando |
|---------|-----------|---------|
| **Menção** | @Bot | `/config gatilho_mention true` |
| **Prefixo** | !comando | `/config gatilho_prefix true` + `/config prefix !` |
| **Interrogação** | ?pergunta | `/config gatilho_question true` |
| **Ambos** | ! OU @Bot | `/config gatilho_both true` |

**Nota**: O prefixo é configurável! Pode ser `!`, `.`, `>`, ou qualquer outro caractere.

---

## 🧬 Sistema de Personas Evolutivas

### O que são?

Personas que **aprendem, adaptam e evoluem** com o tempo, como uma pessoa real.

### Características

#### 1. **Traços de Personalidade**
```python
- Extroversão (0.0 a 1.0)
- Conscienciosidade
- Amabilidade
- Neuroticismo
- Abertura a experiências
- Humor
- Empatia
- Curiosidade
- Formalidade
- Sarcasmo
```

#### 2. **Relacionamentos**
```python
- Familiaridade (quão bem conhece)
- Afinidade (quão gosta)
- Contagem de interações
- Primeiro encontro
- Última interação
- Piadas internas
- Preferências do usuário
```

#### 3. **Memórias Emocionais**
```python
- Eventos marcantes
- Emoção associada (feliz, triste, animado)
- Intensidade
- Contexto
- Timestamp
```

#### 4. **Fatos Aprendidos**
```python
- Informações sobre o mundo
- Preferências dos usuários
- Eventos do servidor
- Tópicos de interesse
```

#### 5. **Opiniões Formadas**
```python
- Opiniões sobre tópicos
- Confiança na opinião
- Evolução das opiniões
```

### Como Criar

```
/persona evolutiva criar
  nome: "Meu Amigo Virtual"
  base_prompt: "Você é um amigo descontraído que gosta de conversar..."
```

### Como Funciona a Evolução

```
1. Interação com usuário
   ↓
2. Análise de sentimento
   ↓
3. Atualização de relacionamento
   ↓
4. Possível memória emocional
   ↓
5. Aprendizado de fatos
   ↓
6. Ajuste de traços (lento)
   ↓
7. Formação de opiniões
```

---

## 🖼️ Visão Multimodal (Imagens, Áudio, Vídeo)

### Imagens

**Personas/GPTs podem ver imagens** quando:
1. Imagem é anexada à mensagem
2. Imagem é mencionada no contexto
3. Usuário pede análise

**Como funciona**:
```python
if message.attachments:
    for attachment in message.attachments:
        if attachment.content_type.startswith("image/"):
            # Processar imagem com vision model
            description = await analyze_image(attachment.url)
            # Incluir na resposta
```

### Áudio

**Personas podem ouvir áudio**:
- Transcrição automática
- Análise de conteúdo
- Resposta contextual

### Vídeos

**Personas podem ver vídeos de forma inteligente**:
```python
# Limitações para não "escaralhar"
- Máximo 5 minutos de vídeo
- Análise de frames-chave
- Resumo do conteúdo
- Reação contextual (não frame a frame)
```

---

## 🔧 Configurações

### Configuração do Dono

```yaml
owner:
  user_id: 123456789012345678  # Seu ID do Discord
```

**Comandos exclusivos**:
- `/owner broadcast` - Envia mensagem para todos os servidores
- `/owner shutdown` - Desliga o bot
- `/owner eval` - Executa código Python
- `/owner sql` - Executa SQL no banco
- `/owner stats` - Estatísticas globais

### Configuração por Servidor

```yaml
guild_defaults:
  model: "openai/gpt-4o-mini"
  system_prompt: "Você é o assistente deste servidor!"
  
  triggers:
    reply_to_bot: true        # Sempre ativo
    on_mention: true
    on_prefix: false
    prefix: "!"
    on_question: false
    chatbot_mode: false
```

### LLMs Locais

```yaml
providers:
  ollama:
    enabled: true
    base_url: "http://localhost:11434/v1"
    models:
      - name: "llama3-local"
        id: "llama3"
```

---

## 📋 Funcionalidades Implementadas

### Do ideias.md implementadas:

| # | Funcionalidade | Status |
|---|----------------|--------|
| 2 | Dashboard Web | 🔄 Parcial |
| 4 | Agentes Autônomos | ✅ Modo Interativo |
| 5 | Fine-tuning | 🔄 Personas Evolutivas |
| 7 | RAG Avançado | ✅ Múltiplos backends |
| 8 | Multi-modal | ✅ Imagens, áudio |
| 9 | Integrações | 🔄 Google Search |
| 11 | Sistema de Plugins | 🔄 Estrutura pronta |
| 12 | Missões/Quests | 📋 Planejado |
| 17 | Temas de embed | 🔄 Parcial |
| 20 | Embeds avançados | ✅ Paginação |
| 21 | Analytics | ✅ Estatísticas |
| 25 | Backup automático | ✅ |
| 26 | Rate limiting | ✅ |
| 27 | Multi-idioma | 🔄 Detecção automática |
| 28 | Tradução | ✅ Comando /traduzir |
| 38 | Caching | 🔄 Parcial |
| 39 | Otimização | ✅ Índices no BD |

---

## 🚀 Comandos Principais

### Chat
- `/chat <mensagem>` - Conversar com o bot
- `/limpar` - Limpar histórico
- `/historico` - Ver estatísticas

### Configuração
- `/config painel` - Painel interativo
- `/config ativar` - Ativar bot no canal
- `/config modo <modo>` - Mudar modo
- `/config gatilho_mention <true/false>`
- `/config gatilho_prefix <true/false>`
- `/config prefix <caractere>`

### Modelos
- `/modelo menu` - Menu interativo
- `/modelo usar <nome>` - Selecionar modelo
- `/modelo adicionar` - Adicionar modelo

### Personas
- `/persona` - Menu de personas
- `/persona usar <nome>` - Ativar persona
- `/persona criar` - Criar persona
- `/persona evolutiva` - Criar persona evolutiva

### Modos
- `/modo normal` - Modo normal
- `/modo assistant` - Modo Assistant
- `/modo chatbot` - Modo chatbot
- `/modo interativo` - Modo interativo
- `/modo roleplay` - Modo roleplay

### Imagens
- `/imagem <prompt>` - Gerar imagem
- `/cotas` - Ver cotas

### Loja
- `/loja itens` - Ver itens
- `/loja comprar` - Comprar item
- `/loja daily` - Recompensa diária

### Apps
- `/traduzir` - Traduzir texto
- `/resumir` - Resumir conversa
- `/analisar` - Analisar sentimento

---

## 🎨 Estrutura do Projeto

```
discord-bot-v2/
├── bot.py                      # Ponto de entrada
├── config-example.yaml         # Configuração de exemplo
│
├── core/                       # Núcleo do bot
│   ├── config.py              # Configurações
│   ├── bot_instance.py        # Instância principal
│   ├── modes.py               # Modos de operação ⭐
│   └── evolving_persona.py    # Personas evolutivas ⭐
│
├── cogs/                       # Módulos de comandos
│   ├── chat_commands.py       # Comandos de chat
│   ├── config_commands.py     # Configurações
│   ├── model_commands.py      # Modelos
│   ├── model_menu.py          # Menu de modelos ⭐
│   ├── persona_commands.py    # Personas
│   ├── persona_menu.py        # Menu de personas ⭐
│   ├── image_commands.py      # Imagens
│   ├── shop_commands.py       # Loja
│   ├── memory_commands.py     # Memória
│   ├── file_commands.py       # Arquivos
│   ├── utility_commands.py    # Utilidades
│   ├── apps_commands.py       # Apps
│   ├── admin_commands.py      # Admin
│   └── owner_commands.py      # Dono ⭐
│
├── database/                   # Banco de dados
│   └── manager.py             # Gerenciador
│
├── providers/                  # Provedores LLM
│   └── manager.py             # Gerenciador
│
└── utils/                      # Utilitários
    ├── logger.py
    ├── status_manager.py
    ├── permission_checker.py
    └── message_processor.py
```

---

## 💡 Exemplos de Uso

### Exemplo 1: Bot que Participa Naturalmente
```
1. /config ativar
2. /modo chatbot
3. /config sensibilidade normal

Resultado: Bot participa das conversas sem precisar ser mencionado
```

### Exemplo 2: Persona Evolutiva
```
1. /persona evolutiva criar
   nome: "Carlos"
   base: "Você é Carlos, um entusiasta de tecnologia..."

2. Conversar normalmente

3. Depois de algumas semanas:
   - Carlos lembra que você gosta de Python
   - Tem opinião sobre frameworks
   - Tem afinidade com você
```

### Exemplo 3: Modo Assistant com Ferramentas
```
1. /config assistente asst_abc123
2. /modo assistant
3. "Calcule a integral de x^2"
   → Bot usa code_interpreter
```

---

## 📞 Suporte

Dúvidas? Consulte:
- `README.md` - Documentação geral
- `DOCUMENTACAO_PERSONAS.md` - Sistema de personas
- `IDEIAS_MELHORIAS.md` - Ideias futuras
- `GUIA_RAPIDO.md` - Guia rápido

---

**Versão**: 2.0  
**Última atualização**: 2025
