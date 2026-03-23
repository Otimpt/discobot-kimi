# 🚀 Guia Rápido - Discord AI Bot v2

## ⚡ Instalação em 3 Passos

### 1. Instale as dependências
```bash
pip install -r requirements.txt
```

### 2. Configure o bot
```bash
# Copie o exemplo
cp config-example.yaml config.yaml

# Edite com suas chaves
nano config.yaml
```

**Mínimo necessário:**
```yaml
bot:
  token: "seu-token-discord-aqui"

providers:
  openai:
    enabled: true
    api_key: "sua-chave-openai"
```

### 3. Inicie
```bash
python bot.py
```

---

## 🎮 Comandos Principais

### Configurar Canal
```
/config ativar                    # Ativa o bot no canal
/config painel                    # Painel interativo completo
/config modo smart                # Modo inteligente
/config gatilhos                  # Configurar como o bot responde
```

### Escolher Modelo
```
/modelo menu                      # Menu interativo de modelos
/modelo usar gpt-4o               # Usar GPT-4o
/modelo usar llama3-local         # Usar LLM local
```

### Personas
```
/persona listar                   # Ver personas disponíveis
/persona criar                    # Criar nova persona
/persona usar NomeDaPersona       # Ativar persona
/persona parar                    # Desativar persona
```

### Chat
```
/chat Olá, como vai?              # Conversar com o bot
/limpar                           # Limpar histórico
/imagem um gato astronauta        # Gerar imagem
```

### Loja
```
/loja itens                       # Ver itens disponíveis
/loja daily                       # Pegar recompensa diária
/loja saldo                       # Ver seu saldo
/top                              # Ranking
```

---

## 🔧 Configurações Avançadas

### Usar LLM Local (Ollama)

```bash
# 1. Instale Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Baixe um modelo
ollama pull llama3

# 3. Inicie o servidor
ollama serve
```

```yaml
# config.yaml
providers:
  ollama:
    enabled: true
    base_url: "http://localhost:11434/v1"
    models:
      - name: "llama3-local"
        id: "llama3"
```

### Configurar Dono do Bot

```yaml
# config.yaml
owner:
  user_id: 123456789012345678  # Seu ID do Discord
```

**Comandos exclusivos do dono:**
```
/owner broadcast Olá a todos!     # Envia para todos os servidores
/owner shutdown                   # Desliga o bot
/owner eval print("teste")        # Executa Python
/owner stats                      # Estatísticas globais
```

### Configurar Gatilhos

```yaml
# config.yaml
guild_defaults:
  triggers:
    reply_to_bot: true       # Sempre responder em reply
    on_mention: true         # Responder quando marcado
    on_prefix: false         # Responder com !
    prefix: "!"
    on_question: false       # Responder quando começa com ?
    chatbot_mode: false      # Modo chatbot (IA decide)
```

---

## 🎭 Criando uma Persona

### Exemplo: Professor de Python

```
/persona criar
  nome: ProfessorPython
  prompt: |
    Você é um professor experiente de Python. Explique conceitos
    de forma clara e didática, use exemplos práticos, e incentive
    o aprendizado. Responda como se estivesse ensinando um aluno
    iniciante com paciência.
  descricao: Professor paciente de Python
```

### Usar:
```
/persona usar ProfessorPython
```

Agora o bot responde como um professor! 🎓

---

## 📁 Estrutura de Arquivos

```
discord-bot-v2/
├── bot.py                    # Início do bot
├── config-example.yaml       # Configuração de exemplo
├── requirements.txt          # Dependências
│
├── core/                     # Núcleo do bot
│   ├── config.py            # Configurações
│   └── bot_instance.py      # Instância principal
│
├── cogs/                     # Comandos (13 módulos!)
│   ├── chat_commands.py
│   ├── config_commands.py
│   ├── model_commands.py
│   ├── model_menu.py        # ⭐ NOVO: Menu de modelos
│   ├── persona_commands.py
│   ├── image_commands.py
│   ├── shop_commands.py
│   ├── memory_commands.py
│   ├── file_commands.py
│   ├── utility_commands.py
│   ├── apps_commands.py
│   ├── admin_commands.py
│   └── owner_commands.py    # ⭐ NOVO: Comandos do dono
│
├── database/                 # Banco de dados
│   └── manager.py
│
├── providers/                # Gerenciador de LLMs
│   └── manager.py
│
└── utils/                    # Utilitários
    ├── logger.py
    ├── status_manager.py
    ├── permission_checker.py
    └── message_processor.py
```

---

## 🔥 Dicas Pro

### 1. Ativar modo chatbot (responde sem gatilhos)
```
/config modo fluido
```

### 2. Usar modelo mais barato para tarefas simples
```
/modelo usar gpt-4o-mini
```

### 3. Criar persona para cada canal
```
# Canal #python
/persona usar ProfessorPython

# Canal #geral
/persona usar Amigavel
```

### 4. Configurar por servidor
```
# Cada servidor tem configurações independentes!
# Use /config painel para configurar visualmente
```

---

## ❓ Solução de Problemas

### Bot não responde
1. Verifique se está ativo: `/config ativar`
2. Verifique gatilhos: `/config info`
3. Verifique permissões do bot no Discord

### Erro de API
1. Verifique chaves no config.yaml
2. Verifique se provedor está habilitado
3. Veja logs: `data/logs/bot_*.log`

### LLM local não funciona
1. Verifique se Ollama está rodando: `ollama list`
2. Verifique URL no config.yaml
3. Teste: `curl http://localhost:11434/api/tags`

---

## 📚 Documentação Completa

- `README.md` - Documentação geral
- `DOCUMENTACAO_PERSONAS.md` - Tudo sobre personas
- `IDEIAS_MELHORIAS.md` - Ideias futuras
- `RESUMO_MELHORIAS.md` - Resumo das melhorias
- `config-example.yaml` - Configuração comentada

---

**Pronto para usar!** 🚀

Dúvidas? Veja a documentação ou abra uma issue!
