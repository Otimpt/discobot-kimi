# 🧠 Sistema de Memória V2 - Inteligente e Humana

O bot tem uma memória que funciona **exatamente como a humana**, com 4 camadas e comportamentos inteligentes!

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MEMÓRIA DO BOT (4 Camadas)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  PERMANENTE (NUNCA esquece!)                                        │   │
│   │  • Tradições do servidor                                            │   │
│   │  • Fatos mencionados 20+ vezes                                      │   │
│   │  • Informações cruciais                                             │   │
│   │  • Relacionamentos importantes                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    ↑                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  LONGO PRAZO (6+ meses)                                             │   │
│   │  • Aniversários, nomes, preferências                                │   │
│   │  • Piadas internas engraçadas                                       │   │
│   │  • Eventos importantes                                              │   │
│   │  • → ESQUECE se não mencionado em 6 meses!                          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    ↑                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  MÉDIO PRAZO (Resumos)                                              │   │
│   │  • Resumos de conversas antigas                                     │   │
│   │  • Pontos importantes                                               │   │
│   │  • → Promovido se acessado 5+ vezes                                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    ↑                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  CURTO PRAZO (1-3 dias)                                             │   │
│   │  • Todas as conversas recentes                                      │   │
│   │  • Contexto da conversa atual                                       │   │
│   │  • → Resumido em 3 dias                                             │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Novidades da V2

### **1. Memória Pula Etapas!**

Memórias importantes podem ir **direto** para longo prazo, sem passar pelo médio:

| Tipo de Memória | Importância Mínima | Vai Direto Para |
|-----------------|-------------------|-----------------|
| Fato importante | 0.8+ | Longo Prazo |
| Info de usuário (nome, aniversário) | 0.7+ | Longo Prazo |
| Info do servidor | 0.75+ | Longo Prazo |
| Piada interna muito engraçada | 0.85+ | Longo Prazo |
| Evento importante | 0.8+ | Longo Prazo |
| Preferência | 0.7+ | Longo Prazo |
| Qualquer coisa | 0.9+ | Longo Prazo |

### **2. Memória PERMANENTE (Nunca Esquece!)**

O bot pode ter memórias que **nunca** são apagadas:

```
Quando vira permanente:
• Mencionada 20+ vezes (virou tradição!)
• Informação fundamental do servidor
• Relacionamento importante
• Importância 0.95+
```

**Exemplo:**
```
Usuário: O aniversário do servidor é 15/03!
Bot: Anotado! [vai direto para longo prazo]

[6 meses depois...]
Usuário: Quando é o aniversário do servidor?
Bot: 15/03! [ainda lembra]

[1 ano depois, mencionado 20+ vezes...]
Bot: 15/03! [agora é PERMANENTE - nunca esquece!]
```

### **3. Cross-Server Memory (Chance Rara!)**

O bot pode "reconhecer" alguém de outro servidor!

```
[Servidor A - há 6 meses]
João: Eu amo chocolate!
Bot: Anotado! João ama chocolate

[Bot entra no Servidor B hoje]
João: Oi bot!
Bot: Oi João! Ainda gosta de chocolate? 😊

[Cross-server memory ativada! 5% de chance]
```

**Como funciona:**
- Quando o bot vê alguém que conhece de outro lugar
- 5% de chance de trazer 1-3 memórias sutis
- O bot age como se "lembrasse" da pessoa
- Memórias são marcadas como "cross-server"

### **4. Memória Separada por Servidor**

Cada servidor tem suas **próprias** memórias isoladas:

```
Servidor A:
  - Memórias sobre usuários do Servidor A
  - Piadas internas do Servidor A
  - Eventos do Servidor A

Servidor B:
  - Memórias sobre usuários do Servidor B
  - Piadas internas do Servidor B
  - Eventos do Servidor B

[Memórias são COMPLETAMENTE separadas!]
```

---

## 📋 Tipos de Memória

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| `conversation` | Conversa normal | "Oi bot!" |
| `fact` | Fato importante | "O servidor foi criado em 2020" |
| `joke` | Piada interna | "A piada do peixe" |
| `user_info` | Info sobre usuário | "João gosta de pizza" |
| `server_info` | Info do servidor | "Regras: não spam" |
| `preference` | Preferência | "Maria prefere café" |
| `event` | Evento | "Festa no sábado" |
| `quote` | Citação | "'Isso é incrível!' - João" |
| `relationship` | Relacionamento | "João e Maria são amigos" |
| `learned` | Algo aprendido | "Python é uma linguagem" |

---

## 🔄 Fluxo Completo

```
Nova mensagem
     │
     ▼
┌────────────────────────────────────────────────────────────┐
│ 1. Classifica tipo de memória                              │
│    • Fato? → Importância alta                              │
│    • Conversa? → Importância normal                        │
└────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────┐
│ 2. Decide onde armazenar                                   │
│    • Importância >= 0.9? → PERMANENTE                      │
│    • Tipo importante? → LONGO PRAZO direto                 │
│    • Normal? → CURTO PRAZO                                 │
└────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────┐
│ 3. Evolução natural                                        │
│                                                              │
│    CURTO (3 dias) ──resumo──→ MÉDIO ──acesso 5x──→ LONGO  │
│         │                                                    │
│         └──importante──→ LONGO (direto!)                    │
│                                                              │
│    LONGO (6 meses) ──não acessado──→ [ESQUECE]             │
│         │                                                    │
│         └──20+ acessos──→ PERMANENTE (nunca esquece!)       │
└────────────────────────────────────────────────────────────┘
```

---

## 💡 Exemplos Práticos

### **Exemplo 1: Fato Vai Direto para Longo Prazo**

```
Usuário: O nome do servidor é "Gamers Unidos"
Bot: [detecta: server_info, importância: 0.85]
Bot: Anotado! Nome do servidor: "Gamers Unidos"

[Armazenado DIRETO em LONGO PRAZO]

[1 ano depois...]
Usuário: Qual o nome do servidor?
Bot: "Gamers Unidos"!
```

### **Exemplo 2: Tradição Vira Permanente**

```
Dia 1:
Usuário: Sexta-feira é dia de filme!
Bot: Anotado!

Dia 2-20:
[Usuário menciona "sexta de filme" várias vezes]

Dia 21:
Bot: [Promovido para PERMANENTE!]

[5 anos depois...]
Usuário: Lembra das sextas de filme?
Bot: Claro! Sexta-feira é dia de filme! 🎬
[Bot NUNCA esquece!]
```

### **Exemplo 3: Esquecimento Natural**

```
Dia 1:
Usuário: Ontem eu comi sushi
Bot: Legal!

[Armazenado em CURTO PRAZO]

Dia 4:
[Resumido para MÉDIO PRAZO]

Dia 30:
[Nunca mais mencionado]

Dia 200:
[Apagado - bot esqueceu]

Usuário: Lembra quando eu comi sushi?
Bot: Não lembro... quando foi? 🤔
```

### **Exemplo 4: Cross-Server Memory**

```
[Servidor A - 6 meses atrás]
Maria: Eu sou professora de matemática
Bot: Que legal! Professora Maria 📐

[Bot entra no Servidor B]
Maria: Oi bot, sou nova aqui!
Bot: Oi Maria! Ainda dando aulas de matemática?

[5% de chance - Cross-server ativado!]
Maria: Como você sabe??
Bot: Ah, só um palpite! 😊
```

---

## ⚙️ Configuração

### **Básica (SQLite)**

```yaml
memory:
  tiers:
    short_term:
      retention_days: 3
      provider: "sqlite"
    
    medium_term:
      provider: "sqlite"
    
    long_term:
      retention_months: 6
      min_importance: 0.6
      min_access_count: 5
      provider: "sqlite"
    
    permanent:
      provider: "sqlite"  # Memórias permanentes
```

### **Avançada (Qdrant Cloud)**

```yaml
memory:
  tiers:
    short_term:
      provider: "qdrant"
      config:
        url: "https://seu-cluster.cloud.qdrant.io"
        api_key: "${QDRANT_API_KEY}"
    
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
    
    permanent:
      provider: "qdrant"  # Memórias nunca apagadas
      config:
        url: "https://seu-cluster.cloud.qdrant.io"
        api_key: "${QDRANT_API_KEY}"
```

---

## ⌨️ Comandos

```bash
# Ver estatísticas de memória
/memoria status

# Ver memórias de um usuário
/memoria usuario @joao

# Ver memórias permanentes
/memoria permanentes

# Limpar memórias (bot esquece!)
/limpar memoria curto      # Esquece conversas recentes
/limpar memoria medio      # Esquece resumos
/limpar memoria longo      # Esquece memórias antigas
/limpar memoria tudo       # ESQUECE TUDO!

# Forçar manutenção (dono)
/owner memoria manutencao

# Ver cross-server memories
/owner memoria cross-server
```

---

## 📊 Estatísticas

```
/memoria status

📊 Estatísticas de Memória

Servidor: Meu Servidor

Camadas:
  📝 Curto Prazo: 150 memórias (3 dias)
  📚 Médio Prazo: 45 memórias (resumos)
  💎 Longo Prazo: 23 memórias (6 meses)
  ⭐ Permanentes: 5 memórias (NUNCA esquece!)

Tipos:
  💬 Conversas: 120
  📋 Fatos: 30
  😂 Piadas: 15
  👤 User Info: 28
  🏠 Server Info: 12
  ⭐ Outros: 18

Cross-Server:
  🌐 Memórias compartilhadas: 3
  👥 Usuários reconhecidos: 5
```

---

## ❓ FAQ

### **Memória de longo prazo é backup?**
**NÃO!** São memórias DIFERENTES que foram promovidas porque são importantes.

### **Como algo vira permanente?**
- Mencionado 20+ vezes
- Importância 0.95+
- Informação fundamental

### **Cross-server funciona sempre?**
Não! Só 5% de chance quando encontra alguém conhecido.

### **Posso fazer o bot esquecer algo específico?**
Não diretamente, mas `/limpar memoria` apaga camadas inteiras.

### **Memórias são separadas por servidor?**
Sim! Cada servidor tem memórias completamente isoladas.

---

## 🔧 discord.py 2.5.0+

O bot usa a versão mais recente do discord.py com:
- Suporte a novos recursos do Discord
- Melhor performance
- Novos tipos de interações
- Webhooks aprimorados
- Threads melhoradas

```
pip install discord.py>=2.5.0
```
