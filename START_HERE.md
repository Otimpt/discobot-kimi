# 🚀 Começando com o Discord AI Bot v2

## Instalação Rápida

### 1. Instale as dependências

```bash
pip install -r requirements.txt
```

Ou use o script de setup:

```bash
python setup.py
```

### 2. Configure o bot

**Opção A: Arquivo .env (Recomendado)**

```bash
cp .env.example .env
# Edite .env com suas chaves
```

**Opção B: Arquivo config.yaml**

```bash
cp config-example.yaml config.yaml
# Edite config.yaml com suas configurações
```

**Opção C: Variáveis de ambiente**

```bash
export DISCORD_BOT_TOKEN="seu-token"
export OPENAI_API_KEY="sua-chave"
```

### 3. Inicie o bot

```bash
python bot.py
```

## ⚙️ Configuração Mínima

Você precisa de pelo menos:

1. **Discord Bot Token**
   - Vá em https://discord.com/developers/applications
   - Crie uma nova aplicação
   - Vá em "Bot" e copie o token

2. **OpenAI API Key** (para funcionalidades de IA)
   - Vá em https://platform.openai.com/api-keys
   - Crie uma nova chave API

## 🎯 Primeiros Passos

1. **Convide o bot para seu servidor**
   - No Discord Developer Portal, vá em OAuth2 > URL Generator
   - Selecione scopes: `bot`, `applications.commands`
   - Selecione permissões: `Send Messages`, `Read Messages`, etc.
   - Copie e abra a URL

2. **Configure um canal**
   ```
   /config ativar
   /config painel
   ```

3. **Teste o bot**
   ```
   /chat Olá, como vai?
   ```

## 📚 Documentação Completa

Veja [README.md](README.md) para documentação completa.

## 🆘 Suporte

Se encontrar problemas:
1. Verifique os logs em `data/logs/`
2. Verifique se todas as dependências estão instaladas
3. Verifique se as chaves API estão corretas

---

**Divirta-se! 🤖**
