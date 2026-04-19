# 🔥 Bot de Ofertas Masculinas — Telegram

Bot que busca ofertas de roupas, tênis, suplementos e acessórios masculinos na Shopee e posta automaticamente no seu canal do Telegram a cada 15 minutos (configurável).

---

## O que você precisa (tudo gratuito)

- Conta no Telegram
- Conta no GitHub (github.com) — para hospedar o código
- Conta no Railway (railway.app) — para rodar o bot 24/7 grátis
- Cadastro no programa de afiliados da Shopee

---

## PASSO 1 — Criar o bot no Telegram

1. Abra o Telegram e procure por **@BotFather**
2. Digite `/newbot`
3. Escolha um nome para o bot (ex: `Ofertas Masculinas Bot`)
4. Escolha um username (ex: `ofertasmasculinasbot`)
5. O BotFather vai te dar um **token** — guarde esse token, parece assim:
   ```
   7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

---

## PASSO 2 — Criar o canal no Telegram

1. No Telegram, toque em **Nova Mensagem → Novo Canal**
2. Dê um nome (ex: `Ofertas Masculinas BR`)
3. Escolha **Público** e defina o username (ex: `@ofertasmasculinasbr`)
4. **Adicione o seu bot como administrador do canal:**
   - Vá nas configurações do canal
   - Administradores → Adicionar Administrador
   - Busque pelo username do seu bot
   - Dê permissão para **Enviar Mensagens**

---

## PASSO 3 — Cadastrar nos programas de afiliados (grátis)

### Shopee Afiliados (recomendado — até 14% de comissão)
1. Acesse: https://affiliate.shopee.com.br
2. Clique em "Inscrever-se"
3. Preencha seus dados e aguarde aprovação (3-5 dias úteis)
4. Após aprovado, acesse o painel e copie seus links de afiliado

### Parceiro Magalu (aprovação imediata — até 12%)
1. Acesse: https://parceiromagalu.com.br
2. Crie sua conta com CPF
3. Aprovação na hora

### Amazon Afiliados (até 10%)
1. Acesse: https://afiliados.amazon.com.br
2. Cadastre-se gratuitamente
3. Após aprovação, você receberá sua **tag de afiliado** (ex: `seutag-20`)

---

## PASSO 4 — Subir o código no GitHub

1. Crie uma conta em **github.com** se não tiver
2. Clique em **New Repository** → nome: `telegram-ofertas-bot`
3. Faça upload de todos os arquivos desta pasta OU use os comandos:

```bash
cd telegram-ofertas-bot
git init
git add .
git commit -m "primeiro commit"
git remote add origin https://github.com/SEU_USUARIO/telegram-ofertas-bot.git
git push -u origin main
```

---

## PASSO 5 — Deploy no Railway (grátis)

1. Acesse **railway.app** e crie conta (pode usar login do GitHub)
2. Clique em **New Project → Deploy from GitHub repo**
3. Selecione o repositório `telegram-ofertas-bot`
4. O Railway vai detectar o Python automaticamente

### Configurar as variáveis de ambiente no Railway:
No painel do projeto clique em **Variables** e adicione:

| Variável | Valor |
|---|---|
| `BOT_TOKEN` | Token que o BotFather te deu |
| `CHANNEL_ID` | `@username_do_seu_canal` |
| `INTERVAL_MINUTES` | `15` |
| `AMAZON_TAG` | Sua tag de afiliado Amazon (opcional) |

5. Clique em **Deploy** — o bot vai iniciar automaticamente!

---

## PASSO 6 — Verificar se está funcionando

- Abra o Railway e clique em **Logs** para ver o bot rodando
- No seu canal do Telegram, deve aparecer a mensagem de boas-vindas
- A cada 15 minutos uma nova oferta será postada automaticamente

---

## Personalização

### Mudar o intervalo de postagem
No Railway, altere a variável `INTERVAL_MINUTES` para o valor desejado.

### Adicionar/remover categorias de produtos
No arquivo `bot.py`, edite a lista `SHOPEE_KEYWORDS`:
```python
SHOPEE_KEYWORDS = [
    "camiseta masculina",
    "tênis masculino",
    # adicione ou remova itens aqui
]
```

### Criar bot para outros nichos
Copie o projeto e altere apenas:
- O `CHANNEL_ID` para o novo canal
- A lista `SHOPEE_KEYWORDS` para o novo nicho (ex: cosméticos, utensílios, tecnologia)

---

## Estrutura dos arquivos

```
telegram-ofertas-bot/
├── bot.py              ← código principal do bot
├── requirements.txt    ← dependências Python
├── railway.toml        ← configuração do Railway
├── .env.example        ← exemplo de variáveis de ambiente
├── .gitignore          ← arquivos ignorados pelo git
└── README.md           ← este arquivo
```

---

## Suporte

Se der algum erro nos logs do Railway, os mais comuns são:

- **`KeyError: BOT_TOKEN`** → Variável de ambiente não configurada no Railway
- **`Unauthorized`** → Token do bot está errado
- **`Chat not found`** → CHANNEL_ID errado ou bot não é admin do canal
- **`Not enough rights`** → Bot precisa de permissão de administrador no canal
