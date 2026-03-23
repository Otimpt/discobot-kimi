# 🧠 Sistema de Memória Hierárquica Inteligente

O bot usa um sistema de memória que **imita a memória humana**, não é apenas backup! Cada camada contém memórias **diferentes** e tem uma função específica.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MEMÓRIA HUMANA vs MEMÓRIA DO BOT                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   MEMÓRIA HUMANA                    MEMÓRIA DO BOT                          │
│   ════════════════                  ════════════════                        │
│                                                                             │
│   ┌──────────────┐                 ┌──────────────┐                         │
│   │  CURTO       │                 │  CURTO       │                         │
│   │  PRAZO       │                 │  PRAZO       │                         │
│   │              │                 │              │                         │
│   │ • O que você │                 │ • Todas as   │                         │
│   │   almoçou    │                 │   conversas  │                         │
│   │   ontem      │                 │   recentes   │                         │
│   │ • Conversa   │                 │ • Detalhes   │                         │
│   │   de hoje    │                 │   completos  │                         │
│   │              │                 │              │                         │
│   │ → Esquece    │                 │ → Resumida   │                         │
│   │   em 3 dias  │                 │   em 3 dias  │                         │
│   └──────┬───────┘                 └──────┬───────┘                         │
│          │                                  │                               │
│          ▼                                  ▼                               │
│   ┌──────────────┐                 ┌──────────────┐                         │
│   │  MÉDIO       │                 │  MÉDIO       │                         │
│   │  PRAZO       │                 │  PRAZO       │                         │
│   │              │                 │              │                         │
│   │ • Resumo da  │                 │ • Resumos de │                         │
│   │   semana     │                 │   conversas  │                         │
│   │ • Eventos    │                 │ • Pontos     │                         │
│   │   importantes│                 │   importantes│                         │
│   │              │                 │              │                         │
│   │ → Lembra     │                 │ → Promovido  │                         │
│   │   às vezes   │                 │   se acessado│                         │
│   └──────┬───────┘                 └──────┬───────┘                         │
│          │                                  │                               │
│          ▼                                  ▼                               │
│   ┌──────────────┐                 ┌──────────────┐                         │
│   │  LONGO       │                 │  LONGO       │                         │
│   │  PRAZO       │                 │  PRAZO       │                         │
│   │              │                 │              │                         │
│   │ • Seu nome   │                 │ • Memórias   │                         │
│   │ • Aniversário│                 │   MUITO      │                         │
│   │ • Traumas    │                 │   importantes│                         │
│   │              │                 │ • Muito      │                         │
│   │ → Esquece se │                 │   acessadas  │                         │
│   │   não usa    │                 │              │                         │
│   │   em 6 meses │                 │ → Esquece se │                         │
│   │              │                 │   não usa    │                         │
│   │              │                 │   em 6 meses │                         │
│   └──────────────┘                 └──────────────┘                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Como Funciona (De Verdade!)

### **📝 Curto Prazo (1-3 dias)**
- **Contém**: Todas as conversas recentes, completas e detalhadas
- **Uso**: Respondendo mensagens, mantendo contexto da conversa atual
- **Quando acessa**: SEMPRE que o bot responde
- **O que acontece**: Depois de 3 dias, é **resumida** e vai para médio prazo

### **📚 Médio Prazo (Resumos)**
- **Contém**: Resumos das conversas antigas de curto prazo
- **Uso**: Quando alguém menciona algo do passado recente
- **Quando acessa**: Ocasionalmente, quando relevante
- **O que acontece**: Se acessada muitas vezes, é **promovida** para longo prazo

### **💎 Longo Prazo (6+ meses)**
- **Contém**: Memórias MUITO importantes e MUITO acessadas
- **Uso**: Quando alguém menciona algo importante do passado
- **Quando acessa**: Raramente, só quando muito relevante
- **O que acontece**: Se **NÃO** for acessada em 6 meses, o bot **ESQUECE** (apaga)

> ⚠️ **IMPORTANTE**: Longo prazo NÃO é backup! São memórias diferentes que foram promovidas porque são importantes!

---

## 🔄 Fluxo da Memória

```
Nova conversa
     │
     ▼
┌─────────────┐
│  CURTO      │ ◄── Acessada frequentemente
│  PRAZO      │     (contexto da conversa)
└──────┬──────┘
       │
       │ Após 3 dias
       ▼
┌─────────────┐
│  RESUMO     │ ◄── Criado automaticamente
│  (Médio)    │     (pontos importantes)
└──────┬──────┘
       │
       │ Se acessada 5+ vezes
       │ e importância >= 0.6
       ▼
┌─────────────┐
│  LONGO      │ ◄── Memórias importantes
│  PRAZO      │     (aniversários, preferências, etc)
└──────┬──────┘
       │
       │ Se NÃO acessada em 6 meses
       ▼
    [ESQUECE]  ◄── Apagada permanentemente!
```

---

## 🔌 Provedores Disponíveis

### **LOCAIS** (Grátis, rodam no seu servidor)

| Provedor | Tipo | Embeddings | Melhor Para |
|----------|------|------------|-------------|
| **SQLite** | Banco SQL | ❌ | Iniciantes, simples |
| **Qdrant** | Vector Store | ✅ | Melhor custo-benefício |
| **Chroma** | Vector Store | ✅ | Fácil de usar |
| **Redis** | Cache | ❌ | Velocidade (curto prazo) |

### **NUVEM** (Requer API key)

| Provedor | Tipo | Preço | Link |
|----------|------|-------|------|
| **Qdrant Cloud** | Vector Store | 1GB grátis | https://cloud.qdrant.io |
| **Pinecone** | Vector Store | $0.10/GB/mês | https://pinecone.io |
| **Oracle Cloud** | Cloud | Free tier | https://oracle.com/cloud |

---

## ⚙️ Configurações

### **1. SQLite (Padrão - Funciona sem instalar nada)**

```yaml
memory:
  tiers:
    short_term:
      retention_days: 3
      provider: "sqlite"
      config:
        db_path: "data/memory_short_term.db"
    
    medium_term:
      provider: "sqlite"
      config:
        db_path: "data/memory_medium_term.db"
    
    long_term:
      retention_months: 6
      min_importance: 0.6      # Importância mínima para promoção
      min_access_count: 5      # Acessos mínimos para promoção
      provider: "sqlite"
      config:
        db_path: "data/memory_long_term.db"
```

### **2. Qdrant Local**

```bash
# Instale o Qdrant
docker run -p 6333:6333 qdrant/qdrant
```

```yaml
memory:
  tiers:
    short_term:
      provider: "qdrant"
      config:
        host: "localhost"
        port: 6333
    
    medium_term:
      provider: "qdrant"
      config:
        host: "localhost"
        port: 6333
    
    long_term:
      provider: "qdrant"
      config:
        host: "localhost"
        port: 6333
```

### **3. Qdrant Cloud (Nuvem - 1GB Grátis!)**

1. Crie conta em https://cloud.qdrant.io
2. Crie um cluster
3. Copie a URL e API Key

```yaml
memory:
  tiers:
    short_term:
      provider: "qdrant"
      config:
        url: "https://seu-cluster.cloud.qdrant.io"
        api_key: "${QDRANT_API_KEY}"  # Coloque no .env
    
    medium_term:
      provider: "qdrant"
      config:
        url: "https://seu-cluster.cloud.qdrant.io"
        api_key: "${QDRANT_API_KEY}"
    
    long_term:
      provider: "qdrant"
      config:
        url: "https://seu-cluster.cloud.qdrant.io"
        api_key: "${QDRANT_API_KEY}"
```

### **4. Pinecone**

```yaml
memory:
  tiers:
    short_term:
      provider: "pinecone"
      config:
        api_key: "${PINECONE_API_KEY}"
        environment: "us-west1-gcp"
```

### **5. Configuração Híbrida**

Use provedores diferentes para cada camada:

```yaml
memory:
  tiers:
    # Curto: Redis (rápido, cache)
    short_term:
      retention_days: 3
      provider: "redis"
      config:
        host: "localhost"
        port: 6379
    
    # Médio: Qdrant (embeddings, busca semântica)
    medium_term:
      provider: "qdrant"
      config:
        host: "localhost"
        port: 6333
    
    # Longo: Qdrant Cloud (persistência, backup na nuvem)
    long_term:
      retention_months: 6
      provider: "qdrant"
      config:
        url: "https://seu-cluster.cloud.qdrant.io"
        api_key: "${QDRANT_API_KEY}"
```

---

## 🎛️ Configurações de Filtro por Canal

Você pode configurar memória diferente para cada canal:

```yaml
memory:
  contexts:
    # Canal específico (ID do canal)
    "123456789012345678":
      short_term:
        retention_days: 7  # Mais dias neste canal
        provider: "qdrant"
        config:
          host: "localhost"
          port: 6333
    
    # DM (chat privado) - cada usuário tem seu próprio contexto
    "dm":
      short_term:
        retention_days: 3
        provider: "sqlite"
        config:
          db_path: "data/memory_dm.db"
    
    # Servidor específico (ID do servidor)
    "guild_987654321098765432":
      short_term:
        provider: "redis"
        config:
          host: "localhost"
          port: 6379
```

---

## 🖼️ Cota de Imagens (Por Usuário!)

Sim, a cota de geração de imagem é **por usuário**!

```yaml
image_generation:
  enabled: true
  quotas:
    weekly_default: 5      # 5 imagens por semana por usuário
    max_per_user: 50       # Máximo acumulado
```

### **Como funciona:**
- Cada usuário tem sua própria cota
- Reseta toda semana
- Pode comprar mais na loja
- Dono do bot tem ilimitado

### **Comandos:**
```
/loja daily          # Resgata tokens diários
/loja comprar        # Compra mais gerações
/loja saldo          # Verifica saldo
```

---

## ⌨️ Comandos de Memória

### **Configurar Memória**
```
/config memoria curto sqlite
/config memoria curto qdrant
/config memoria medio qdrant
/config memoria longo qdrant
```

### **Ver Configuração**
```
/config memoria status
```

### **Limpar Memória**
```
/limpar memoria curto    # Limpa curto prazo (conversas recentes)
/limpar memoria medio    # Limpa médio prazo (resumos)
/limpar memoria longo    # Limpa longo prazo (memórias importantes)
/limpar memoria tudo     # Limpa TUDO (o bot esquece tudo!)
```

### **Forçar Manutenção (Dono)**
```
/owner memoria manutencao
```

---

## 📊 Exemplos de Uso

### **Exemplo 1: Conversa Normal**

```
Usuário: Oi bot!
Bot: Oi! Como posso ajudar?

[Memória: "Usuário disse oi" → Curto Prazo]

Usuário: Qual meu nome?
Bot: Você não me disse seu nome ainda!

[Bot busca em Curto, Médio e Longo prazo - não acha]

Usuário: Meu nome é João
Bot: Prazer, João! Vou lembrar disso.

[Memória: "Nome do usuário é João" → Curto Prazo (importância: 0.8)]
```

### **Exemplo 2: Promoção para Longo Prazo**

```
# Dia 1
Usuário: Meu aniversário é 15/03
Bot: Anotado! 15/03

[Memória: "Aniversário: 15/03" → Curto Prazo (importância: 0.9)]

# Dia 2
Usuário: Quando é meu aniversário?
Bot: 15/03!

[Acessada 1x]

# Dia 5
Usuário: Quando é meu aniversário?
Bot: 15/03!

[Acessada 5x - PROMOVIDA para Longo Prazo!]

# 3 meses depois...
Usuário: Quando é meu aniversário?
Bot: 15/03!

[Buscou em Longo Prazo e achou!]

# 7 meses depois (sem mencionar)...
[Memória apagada - bot esqueceu 😢]
```

### **Exemplo 3: Esquecimento**

```
# Dia 1
Usuário: Ontem eu comi pizza
Bot: Legal! Pizza é bom!

[Memória: "Usuário comeu pizza ontem" → Curto Prazo (importância: 0.3)]

# 4 dias depois...
[Curto prazo resumido → Médio prazo]

# 1 mês depois (nunca mais mencionado)...
[Médio prazo não foi acessado - permanece]

# 6 meses depois (nunca mais mencionado)...
[Apagado de Médio prazo - bot esqueceu]

Usuário: Lembra quando eu comi pizza?
Bot: Não lembro... quando foi?
```

---

## ❓ FAQ

### **Longo prazo é backup?**
**NÃO!** Longo prazo contém memórias **diferentes** - só as mais importantes que foram promovidas. Se não forem acessadas em 6 meses, o bot **esquece** (apaga).

### **Posso usar Qdrant na nuvem?**
Sim! Qdrant Cloud dá 1GB grátis. É só usar `url` e `api_key` na configuração.

### **A cota de imagem é por usuário?**
Sim! Cada usuário tem sua própria cota semanal.

### **Posso configurar memória diferente por canal?**
Sim! Use a seção `memory.contexts` no config.yaml.

### **O que acontece se eu mudar de provedor?**
As memórias são migradas automaticamente para o novo provedor.

### **Posso fazer o bot esquecer algo específico?**
Não diretamente, mas você pode usar `/limpar memoria` para apagar camadas inteiras.

### **Como sei qual camada está sendo usada?**
Use `/config memoria status` para ver a configuração atual.

---

## 🔧 Instalação dos Provedores

### **Qdrant Local**
```bash
docker run -p 6333:6333 qdrant/qdrant
```

### **Qdrant Cloud**
1. Acesse https://cloud.qdrant.io
2. Crie uma conta (grátis)
3. Crie um cluster
4. Copie a URL e API Key

### **Chroma**
```bash
pip install chromadb
```

### **Redis**
```bash
docker run -p 6379:6379 redis:latest
```

### **Pinecone**
```bash
pip install pinecone-client
```

---

## 📞 Suporte

Problemas com memória?

1. Verifique logs em `data/logs/`
2. Teste a conexão: `/owner diagnostico memoria`
3. Verifique espaço em disco
4. Confira as permissões de arquivo
