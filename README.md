# 🤖 Discord AI Bot v2

Um bot de Discord avançado e completo com múltiplos modelos de IA, sistema de memória inteligente, modos de operação flexíveis e muito mais.

## ✨ Funcionalidades Principais

### 💬 Chat Inteligente
- **Múltiplos Modelos**: Suporte a OpenAI, Anthropic, Groq, Together, XAI, Mistral, Google Gemini, Ollama e mais
- **Modo Normal**: Chat completion com contexto e memória
- **Modo Assistant**: Integração completa com OpenAI Assistant API
- **Streaming**: Respostas em tempo real

### 🎭 Personas
- Crie personalidades customizadas com system prompts
- Importe/exporte personas em JSON
- Suporte a OpenAI Prompt IDs
- Personas por servidor ou globais

### 🧠 Memória Inteligente
- **Memória de Curto Prazo**: Histórico de conversas
- **Memória de Longo Prazo**: Fatos sobre usuários e servidores
- **Vector Store**: RAG com Pinecone, Qdrant, Redis ou SQLite
- **LangChain**: Integração opcional com LangChain

### 🎨 Geração de Imagens
- DALL-E 3 integrado
- Sistema de cotas semanais configuráveis
- Loja para comprar mais gerações

### 🛒 Sistema de Loja
- Economia com tokens
- Compra de cotas de imagem
- Recompensas diárias
- Transferência entre usuários

### ⚙️ Configurações Avançadas
- **Gatilhos Configuráveis**: Menção, reply, prefixo (!), ou todos
- **Modos de Operação**: Desativado, Inteligente, Fluido, Frenético, Roleplay
- **Por Canal**: Cada canal tem configurações independentes
- **Por Servidor**: Configurações específicas por servidor

### 📁 Gerenciamento de Arquivos
- Upload e download de arquivos
- Sistema de privacidade
- Integração com RAG

### 🔧 Apps Úteis
- Tradução automática
- Resumo de conversas
- Análise de sentimento
- Correção de texto
- Explicações simplificadas

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/discord-bot-v2.git
cd discord-bot-v2
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure o bot

```bash
cp config-example.yaml config.yaml
# Edite config.yaml com suas configurações
```

Ou use variáveis de ambiente:

```bash
export DISCORD_BOT_TOKEN="seu-token-aqui"
export OPENAI_API_KEY="sua-chave-aqui"
```

### 4. Inicie o bot

```bash
python bot.py
```

## 📋 Configuração

### Variáveis de Ambiente

| Variável | Descrição |
|----------|-----------|
| `DISCORD_BOT_TOKEN` | Token do bot Discord |
| `DISCORD_CLIENT_ID` | Client ID do bot |
| `OPENAI_API_KEY` | Chave da API OpenAI |
| `TOGETHER_API_KEY` | Chave da API Together |
| `GROQ_API_KEY` | Chave da API Groq |
| `OPENROUTER_API_KEY` | Chave da API OpenRouter |
| `XAI_API_KEY` | Chave da API XAI |
| `MISTRAL_API_KEY` | Chave da API Mistral |
| `ANTHROPIC_API_KEY` | Chave da API Anthropic |
| `GOOGLE_API_KEY` | Chave da API Google |
| `OPENAI_ASSISTANT_ID` | ID do Assistant OpenAI |
| `GOOGLE_CSE_API_KEY` | Chave do Google Custom Search |
| `GOOGLE_CSE_CX` | ID do mecanismo de busca |
| `PINECONE_API_KEY` | Chave da API Pinecone |
| `REDIS_URL` | URL do Redis |

## 🎮 Comandos

### Chat
- `/chat <mensagem>` - Conversa com o bot
- `/limpar` - Limpa histórico do canal
- `/historico` - Mostra suas estatísticas

### Configuração
- `/config painel` - Painel interativo de configuração
- `/config ativar` - Ativa o bot no canal
- `/config desativar` - Desativa o bot no canal
- `/config modo` - Define modo de operação
- `/config gatilhos` - Define como o bot responde
- `/config memoria` - Ativa/desativa memória
- `/config contexto` - Modo normal ou Assistant
- `/config assistente <id>` - Define Assistant ID

### Modelos
- `/modelo listar` - Lista modelos disponíveis
- `/modelo usar <nome>` - Seleciona modelo
- `/modelo adicionar` - Adiciona modelo customizado
- `/modelo remover <nome>` - Remove modelo
- `/modelo info <nome>` - Informações do modelo

### Personas
- `/persona listar` - Lista personas
- `/persona usar <nome>` - Ativa persona
- `/persona criar` - Cria nova persona
- `/persona apagar <nome>` - Remove persona
- `/persona exportar <nome>` - Exporta persona
- `/persona importar` - Importa persona

### Imagens
- `/imagem <prompt>` - Gera imagem
- `/cotas` - Verifica cotas de imagem

### Loja
- `/loja itens` - Lista itens
- `/loja comprar` - Compra item
- `/loja saldo` - Seu saldo
- `/loja daily` - Recompensa diária
- `/loja transferir` - Transfere tokens
- `/top` - Ranking de tokens

### Arquivos
- `/arquivo enviar` - Envia arquivo
- `/arquivo listar` - Lista arquivos
- `/arquivo baixar <id>` - Baixa arquivo
- `/arquivo apagar <id>` - Remove arquivo

### Memória
- `/memoria adicionar` - Adiciona fato
- `/memoria ver` - Mostra memórias
- `/memoria apagar` - Remove fato
- `/memoria limpar` - Limpa todas as memórias

### Apps
- `/traduzir` - Traduz texto
- `/resumir` - Resume conversa
- `/analisar` - Analisa sentimento
- `/perguntar` - Pergunta sobre texto
- `/corrigir` - Corrige texto
- `/explicar` - Explica conceito

### Utilidades
- `/ajuda` - Mostra ajuda
- `/ping` - Latência do bot
- `/info` - Informações do bot
- `/dado` - Rola dados
- `/moeda` - Joga moeda
- `/sortear` - Sorteia membro
- `/avatar` - Mostra avatar
- `/serverinfo` - Info do servidor
- `/userinfo` - Info do usuário

### Admin
- `/admin tokens` - Adiciona tokens
- `/admin cotas` - Adiciona cotas
- `/admin banir` - Banir usuário
- `/admin desbanir` - Desbanir usuário
- `/admin backup` - Cria backup
- `/admin stats` - Estatísticas

## 🧠 Modos de Operação

| Modo | Descrição |
|------|-----------|
| **Desativado** | Bot não responde |
| **Inteligente** | Responde a menções e replies |
| **Fluido** | Participa ativamente das conversas |
| **Frenético** | Responde a todas as mensagens |
| **Roleplay** | Modo roleplay com persona ativa |

## 🔔 Modos de Gatilho

| Modo | Descrição |
|------|-----------|
| **Menção/Reply** | Responde quando mencionado ou em reply |
| **Prefixo** | Responde a mensagens começando com ! |
| **Todos** | Responde a menções, replies e prefixo |
| **Desativado** | Apenas modo autônomo (chatbot) |

## 📁 Estrutura do Projeto

```
discord-bot-v2/
├── bot.py                 # Arquivo principal
├── requirements.txt       # Dependências
├── config-example.yaml    # Exemplo de configuração
├── README.md             # Este arquivo
│
├── core/                 # Núcleo do bot
│   ├── config.py        # Configurações
│   └── bot_instance.py  # Instância do bot
│
├── cogs/                # Módulos de comandos
│   ├── chat_commands.py
│   ├── config_commands.py
│   ├── model_commands.py
│   ├── persona_commands.py
│   ├── image_commands.py
│   ├── shop_commands.py
│   ├── file_commands.py
│   ├── utility_commands.py
│   ├── apps_commands.py
│   ├── memory_commands.py
│   └── admin_commands.py
│
├── database/            # Banco de dados
│   └── manager.py
│
├── providers/           # Gerenciamento de LLMs
│   └── manager.py
│
├── utils/               # Utilitários
│   ├── logger.py
│   ├── status_manager.py
│   ├── permission_checker.py
│   └── message_processor.py
│
└── data/                # Dados do bot
    ├── uploads/         # Arquivos enviados
    ├── backups/         # Backups do BD
    └── logs/            # Logs
```

## 🔌 Provedores Suportados

- ✅ OpenAI (GPT-4, GPT-4o, GPT-5)
- ✅ Anthropic (Claude)
- ✅ Groq (Llama, Mixtral)
- ✅ Together AI
- ✅ XAI (Grok)
- ✅ Mistral AI
- ✅ Google (Gemini)
- ✅ Cohere
- ✅ Ollama (local)
- ✅ LM Studio (local)
- ✅ OpenRouter

## 🗄️ Vector Stores Suportados

- ✅ SQLite (padrão, embutido)
- ✅ Pinecone
- ✅ Qdrant
- ✅ Redis
- ✅ PostgreSQL + pgvector

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está licenciado sob a licença MIT.

## 💖 Suporte

Se você gostou deste projeto, considere dar uma ⭐ no GitHub!

Para suporte, entre em contato através do Discord ou abra uma issue.

---

**Desenvolvido com ❤️ e ☕**
