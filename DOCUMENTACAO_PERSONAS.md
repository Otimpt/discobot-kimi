# 🎭 Sistema de Personas - Documentação Completa

## O que são Personas?

**Personas** são personalidades/customizações do bot que mudam completamente como ele se comporta, responde e interage. Cada persona tem:

- **Nome único**: Identificador da persona
- **System Prompt**: Instruções que definem a personalidade
- **Prompt ID (opcional)**: ID de prompt da OpenAI
- **Descrição**: Explicação sobre a persona
- **Avatar (opcional)**: Imagem da persona

---

## 🎯 Tipos de Personas

### 1. **Personas Globais**
- Disponíveis em **todos os servidores**
- Apenas o **dono do bot** pode criar
- Exemplos: "Assistente Padrão", "Professor", "Programador"

### 2. **Personas de Servidor**
- Disponíveis **apenas no servidor onde foram criadas**
- **Admins do servidor** podem criar
- Exemplos: "Mascote do Server", "Moderador", "Helper"

### 3. **Personas de Usuário** (futuro)
- Cada usuário pode ter sua própria persona
- Aplica-se apenas às conversas individuais

---

## 📝 Como Funciona

### System Prompt

Quando uma persona está ativa, o **system prompt** dela substitui o padrão:

```
# Sem persona (padrão):
"Você é um assistente de IA amigável e prestativo."

# Com persona "Professor":
"Você é um professor paciente e didático. Explique conceitos de forma 
clara, use exemplos práticos e incentive o aprendizado. Responda como 
se estivesse ensinando um aluno."

# Com persona "Pirata":
"Você é um pirata alegre do século XVIII. Fale com gírias piratas, 
use expressões como 'arr', 'matey', 'ahoy!' e conte histórias de 
grandes aventuras no mar."
```

### Estrutura de uma Persona

```yaml
{
  "name": "nome-da-persona",
  "description": "Descrição curta",
  "system_prompt": "Instruções completas...",
  "prompt_id": "prompt-id-openai-optional",
  "is_global": false,
  "guild_id": 123456789,  # null se global
  "created_by": 987654321,
  "created_at": "2025-01-01T00:00:00"
}
```

---

## 🎮 Comandos

### Criar Persona
```
/persona criar
  nome: "Professor de Python"
  prompt: "Você é um professor experiente de Python..."
  descricao: "Ensina Python de forma didática"
```

### Usar Persona
```
/persona usar nome: "Professor de Python"
```
→ O bot agora responde como um professor de Python!

### Listar Personas
```
/persona listar
```
→ Mostra todas as personas disponíveis (globais + do servidor)

### Parar Persona
```
/persona parar
```
→ Volta ao comportamento padrão

### Exportar Persona
```
/persona exportar nome: "Professor de Python"
```
→ Gera arquivo JSON que pode ser compartilhado

### Importar Persona
```
/persona importar arquivo: professor.json
```
→ Importa uma persona de arquivo JSON

---

## 💡 Exemplos de Personas

### 1. **Assistente Técnico**
```
Nome: TechSupport
Prompt: Você é um técnico de suporte especializado. Responda de 
forma clara e objetiva, use linguagem técnica quando apropriado, 
e sempre ofereça soluções práticas. Se não souber algo, admita 
e sugere onde encontrar a informação.
```

### 2. **Criativo/Brainstorm**
```
Nome: Criativo
Prompt: Você é um parceiro criativo. Ajude a gerar ideias, pense 
fora da caixa, faça conexões inesperadas e incentive a criatividade. 
Use analogias, metáforas e exemplos diversos.
```

### 3. **Conciso/Direto**
```
Nome: Direto
Prompt: Você é extremamente conciso. Responda em poucas palavras, 
vá direto ao ponto, evite floreios. Use bullet points quando 
apropriado.
```

### 4. **Personagem de RPG**
```
Nome: Merlin
Prompt: Você é Merlin, o lendário mago. Fale de forma misteriosa 
e sábia, use referências à magia e ao passado, ocasionalmente 
faça previsões enigmáticas. Mantenha o personagem consistentemente.
```

### 5. **Especialista em Código**
```
Nome: CodeReviewer
Prompt: Você é um desenvolvedor sênior experiente. Revise código 
atentamente, identifique bugs, sugira melhorias de performance, 
e explique as razões por trás das suas recomendações. Use boas 
práticas de programação.
```

---

## 🔄 Como as Personas Afetam as Respostas

### Exemplo 1: Pergunta Simples
**Pergunta**: "O que é uma variável?"

**Sem persona**:
> Uma variável é um espaço na memória do computador usado para armazenar dados.

**Com persona "Professor"**:
> Ótima pergunta! 🎓 Imagine uma variável como uma **caixa etiquetada** onde você pode guardar algo. 
> 
> Por exemplo:
> - Caixa etiquetada "idade" → guarda o número 25
> - Caixa etiquetada "nome" → guarda o texto "Maria"
> 
> Em Python, escrevemos assim:
> ```python
> idade = 25
> nome = "Maria"
> ```
> Quer que eu explique mais alguma coisa?

**Com persona "Pirata"**:
> Arr, matey! Uma variável seja como um **baú do tesouro** com um nome gravado! 🏴‍☠️
> 
> Tu pode guardar ouro (números), mapas (texto), ou qualquer tesouro nesse baú!
> ```python
> ouro = 1000  # Meu tesouro!
> navio = "Perola Negra"
> ```
> Agora vá, marujo, e programe como um verdadeiro corsário!

---

## 🏗️ Arquitetura Técnica

### Banco de Dados

```sql
CREATE TABLE personas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER,              -- NULL = global
    name TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    prompt_id TEXT,                -- OpenAI Prompt ID
    description TEXT,
    avatar_url TEXT,
    is_global BOOLEAN DEFAULT 0,
    created_by INTEGER,
    created_at TIMESTAMP
);
```

### Fluxo de Uso

1. **Criação**:
   ```
   Usuário → /persona criar → Salva no BD
   ```

2. **Ativação**:
   ```
   /persona usar → Salva persona_id em channel_settings
   ```

3. **Processamento de Mensagem**:
   ```
   Mensagem recebida → Verifica persona_id do canal
                     → Busca system_prompt da persona
                     → Envia para LLM com persona
                     → Retorna resposta no estilo da persona
   ```

4. **Desativação**:
   ```
   /persona parar → Remove persona_id das configurações
   ```

---

## 🎨 Prompt ID da OpenAI

### O que é?
O **Prompt ID** é um recurso da OpenAI que permite:
- Versionar prompts
- Usar prompts otimizados
- Compartilhar prompts entre aplicações

### Como usar?
1. Crie um prompt em https://platform.openai.com/prompts
2. Copie o ID do prompt
3. Use ao criar a persona:
   ```
   /persona criar nome: "MinhaPersona" prompt_id: "prompt-abc123"
   ```

### Vantagens:
- ✅ Prompts otimizados pela OpenAI
- ✅ Versionamento automático
- ✅ Métricas de uso
- ✅ Fácil atualização

---

## 📊 Casos de Uso

### Servidor de Programação
- **Persona "CodeReviewer"**: Para revisar código
- **Persona "Debugger"**: Para ajudar com bugs
- **Persona "DocWriter"**: Para escrever documentação

### Servidor de Estudos
- **Persona "Professor"**: Para explicar conceitos
- **Persona "Tutor"**: Para exercícios práticos
- **Persona "Resumidor"**: Para resumir conteúdos

### Servidor de RPG
- **Persona "Mestre"**: Para narrar aventuras
- **Persona "NPC"**: Para personagens específicos
- **Persona "LoreKeeper"**: Para informações do mundo

### Servidor Corporativo
- **Persona "Assistente"**: Para tarefas gerais
- **Persona "Analista"**: Para análise de dados
- **Persona "Redator"**: Para comunicados

---

## 🔮 Futuro do Sistema

### Funcionalidades Planejadas:
1. **Personas Dinâmicas**: Evoluem com base nas interações
2. **Personas de Usuário**: Cada usuário tem sua própria
3. **Personas Temporárias**: Duração limitada (eventos)
4. **Personas com Voz**: Configurações TTS específicas
5. **Personas com Ferramentas**: Conjunto específico de tools
6. **Marketplace**: Compartilhar personas entre servidores

---

## 💡 Dicas para Criar Boas Personas

### ✅ Faça:
- Seja específico nas instruções
- Defina tom e estilo claramente
- Use exemplos no prompt
- Mantenha consistência
- Teste antes de usar

### ❌ Evite:
- Prompts muito longos (perde foco)
- Instruções contraditórias
- Ser muito vago
- Esquecer de testar

---

## 📚 Recursos Adicionais

- [OpenAI Prompt Engineering](https://platform.openai.com/docs/guides/prompt-engineering)
- [Discord Bot Best Practices](https://discord.com/developers/docs/interactions/application-commands)

---

**Versão**: 2.0  
**Última atualização**: 2025
