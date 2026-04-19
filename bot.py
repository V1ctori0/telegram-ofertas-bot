import os
import time
import random
import logging
import requests
import schedule
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

BOT_TOKEN     = os.environ["BOT_TOKEN"]
CHANNEL_ID    = os.environ["CHANNEL_ID"]        # ex: @meucanal ou -100xxxxxxxxx
SHOPEE_APP_ID = os.environ.get("SHOPEE_APP_ID", "")
SHOPEE_SECRET = os.environ.get("SHOPEE_SECRET", "")
AMAZON_TAG    = os.environ.get("AMAZON_TAG", "")  # seu id de afiliado amazon

INTERVAL_MINUTES = int(os.environ.get("INTERVAL_MINUTES", "15"))

# ---------------------------------------------------------------------------
# Scraper de ofertas — usa API pública de cupons/promoções
# ---------------------------------------------------------------------------

SHOPEE_KEYWORDS = [
    "camiseta masculina", "calça masculina", "tênis masculino",
    "bermuda masculina", "suplemento masculino", "whey protein",
    "mochila masculina", "relógio masculino", "perfume masculino",
    "cueca masculina", "polo masculina", "sapato masculino"
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
}


def buscar_ofertas_shopee(keyword: str, limite: int = 5) -> list[dict]:
    """Busca produtos em oferta na Shopee via API pública de busca."""
    try:
        url = "https://shopee.com.br/api/v4/search/search_items"
        params = {
            "by": "relevancy",
            "keyword": keyword,
            "limit": 20,
            "newest": 0,
            "order": "desc",
            "page_type": "search",
            "scenario": "PAGE_GLOBAL_SEARCH",
            "version": 2,
        }
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            log.warning(f"Shopee retornou {resp.status_code} para '{keyword}'")
            return []

        itens = resp.json().get("items", []) or []
        ofertas = []
        for item in itens[:limite]:
            info = item.get("item_basic", {})
            preco_atual = info.get("price", 0) / 100000
            preco_original = info.get("price_before_discount", 0) / 100000
            desconto = info.get("raw_discount", 0)
            nome = info.get("name", "")
            shopid = info.get("shopid", "")
            itemid = info.get("itemid", "")
            vendas = info.get("sold", 0)
            rating = round(info.get("item_rating", {}).get("rating_star", 0), 1)
            imagem = info.get("image", "")
            imagem_url = f"https://cf.shopee.com.br/file/{imagem}" if imagem else ""

            if preco_atual <= 0 or desconto < 10:
                continue

            link = f"https://shopee.com.br/product/{shopid}/{itemid}"
            link_afiliado = gerar_link_afiliado_shopee(link)

            ofertas.append({
                "plataforma": "Shopee",
                "nome": nome,
                "preco_atual": preco_atual,
                "preco_original": preco_original if preco_original > preco_atual else None,
                "desconto": desconto,
                "vendas": vendas,
                "rating": rating,
                "link": link_afiliado,
                "imagem": imagem_url,
            })

        return ofertas

    except Exception as e:
        log.error(f"Erro ao buscar Shopee '{keyword}': {e}")
        return []


def gerar_link_afiliado_shopee(url_produto: str) -> str:
    """
    Gera link de afiliado da Shopee.
    Substitua pela chamada real da API de afiliados Shopee quando tiver credenciais.
    Por ora retorna o link com parâmetro de rastreio customizado.
    """
    if SHOPEE_APP_ID and SHOPEE_SECRET:
        # TODO: implementar assinatura HMAC quando tiver credenciais oficiais
        pass
    # Link limpo com utm para rastreio básico
    sep = "&" if "?" in url_produto else "?"
    return f"{url_produto}{sep}utm_source=bot_telegram&utm_medium=afiliado"


def gerar_link_afiliado_amazon(asin: str) -> str:
    if AMAZON_TAG:
        return f"https://www.amazon.com.br/dp/{asin}?tag={AMAZON_TAG}"
    return f"https://www.amazon.com.br/dp/{asin}"


# ---------------------------------------------------------------------------
# Formatação da mensagem
# ---------------------------------------------------------------------------

EMOJIS_FOGO  = ["🔥", "🚨", "⚡", "💥", "🎯"]
EMOJIS_RELOGIO = ["⏰", "⌛", "🕐"]
EMOJIS_PRODUTO = {
    "tênis": "👟", "sapato": "👞", "mochila": "🎒",
    "relógio": "⌚", "perfume": "🧴", "suplemento": "💪",
    "whey": "💪", "camiseta": "👕", "calça": "👖",
    "bermuda": "🩳", "cueca": "🩲", "polo": "👔",
}


def emoji_produto(nome: str) -> str:
    nome_lower = nome.lower()
    for k, v in EMOJIS_PRODUTO.items():
        if k in nome_lower:
            return v
    return "🛍️"


def formatar_mensagem(oferta: dict) -> str:
    fogo = random.choice(EMOJIS_FOGO)
    relogio = random.choice(EMOJIS_RELOGIO)
    ep = emoji_produto(oferta["nome"])
    nome = oferta["nome"][:60] + ("…" if len(oferta["nome"]) > 60 else "")
    preco = f"R$ {oferta['preco_atual']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    linhas = [
        f"{fogo} *OFERTA MASCULINA* {fogo}",
        "",
        f"{ep} *{nome}*",
        "",
        f"💰 *Por apenas {preco}*",
    ]

    if oferta.get("preco_original"):
        orig = f"R$ {oferta['preco_original']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        linhas.append(f"~~De {orig}~~ ➜ *{oferta['desconto']}% OFF*")

    if oferta.get("rating"):
        linhas.append(f"⭐ {oferta['rating']}/5")

    if oferta.get("vendas"):
        linhas.append(f"📦 {oferta['vendas']:,} vendidos".replace(",", "."))

    linhas += [
        "",
        "✅ Frete grátis em pedidos elegíveis",
        f"{relogio} Oferta por tempo limitado",
        "",
        f"👉 [COMPRAR AGORA]({oferta['link']})",
        "",
        "📲 _Ative as notificações para não perder nenhuma oferta\\!_",
    ]

    return "\n".join(linhas)


# ---------------------------------------------------------------------------
# Envio ao canal
# ---------------------------------------------------------------------------

bot = Bot(token=BOT_TOKEN)


def enviar_oferta(oferta: dict):
    texto = formatar_mensagem(oferta)
    try:
        if oferta.get("imagem"):
            bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=oferta["imagem"],
                caption=texto,
                parse_mode=ParseMode.MARKDOWN_V2,
            )
        else:
            bot.send_message(
                chat_id=CHANNEL_ID,
                text=texto,
                parse_mode=ParseMode.MARKDOWN_V2,
                disable_web_page_preview=False,
            )
        log.info(f"Oferta enviada: {oferta['nome'][:40]}")
    except Exception as e:
        log.error(f"Erro ao enviar mensagem: {e}")
        # fallback sem markdown
        try:
            bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"🔥 OFERTA: {oferta['nome'][:60]}\n💰 R$ {oferta['preco_atual']:.2f}\n👉 {oferta['link']}",
            )
        except Exception as e2:
            log.error(f"Falha no fallback: {e2}")


# ---------------------------------------------------------------------------
# Job principal
# ---------------------------------------------------------------------------

_ultimo_enviado: set[str] = set()


def job_ofertas():
    log.info("Buscando ofertas...")
    keyword = random.choice(SHOPEE_KEYWORDS)
    log.info(f"Keyword: {keyword}")

    ofertas = buscar_ofertas_shopee(keyword, limite=8)

    novas = [o for o in ofertas if o["link"] not in _ultimo_enviado]
    if not novas:
        log.info("Nenhuma oferta nova encontrada.")
        return

    # Escolhe a melhor oferta (maior desconto)
    melhor = sorted(novas, key=lambda x: x["desconto"], reverse=True)[0]
    enviar_oferta(melhor)
    _ultimo_enviado.add(melhor["link"])

    # Evita cache infinito
    if len(_ultimo_enviado) > 500:
        _ultimo_enviado.clear()


def mensagem_boas_vindas():
    try:
        bot.send_message(
            chat_id=CHANNEL_ID,
            text=(
                "👋 *Bot de Ofertas Masculinas online\\!*\n\n"
                "🔥 A partir de agora vou postar as melhores ofertas de:\n"
                "👕 Roupas masculinas\n"
                "👟 Tênis e calçados\n"
                "💪 Suplementos\n"
                "🎒 Acessórios\n\n"
                f"⏱ Novas ofertas a cada {INTERVAL_MINUTES} minutos\\!\n\n"
                "📲 _Ative as notificações e não perca nenhuma oferta\\!_"
            ),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    except Exception as e:
        log.error(f"Erro na mensagem de boas-vindas: {e}")


# ---------------------------------------------------------------------------
# Inicialização
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    log.info("Bot iniciado!")
    mensagem_boas_vindas()

    # Roda imediatamente na primeira vez
    job_ofertas()

    # Agenda para rodar a cada N minutos
    schedule.every(INTERVAL_MINUTES).minutes.do(job_ofertas)

    while True:
        schedule.run_pending()
        time.sleep(30)
