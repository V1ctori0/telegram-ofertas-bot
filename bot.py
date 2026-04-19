import os
import time
import random
import logging
import requests
import schedule
import asyncio
from telegram import Bot
from telegram.constants import ParseMode

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]
INTERVAL_MINUTES = int(os.environ.get("INTERVAL_MINUTES", "15"))

bot = Bot(token=BOT_TOKEN)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

SHOPEE_KEYWORDS = [
    "tênis masculino",
    "sapato masculino",
    "chinelo masculino"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

# ---------------------------------------------------------------------------
# BUSCAR OFERTAS
# ---------------------------------------------------------------------------

def buscar_ofertas_shopee(keyword):
    try:
        url = "https://shopee.com.br/api/v4/search/search_items"
        params = {
            "keyword": keyword,
            "limit": 10,
        }

        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)

        if resp.status_code != 200:
            log.warning(f"Shopee bloqueou ({resp.status_code})")
            return []

        itens = resp.json().get("items", [])
        ofertas = []

        for item in itens:
            info = item.get("item_basic", {})

            preco = info.get("price", 0) / 100000
            nome = info.get("name", "")
            shopid = info.get("shopid")
            itemid = info.get("itemid")

            if preco <= 0:
                continue

            link = f"https://shopee.com.br/product/{shopid}/{itemid}"

            ofertas.append({
                "nome": nome,
                "preco": preco,
                "link": link
            })

        return ofertas

    except Exception as e:
        log.error(f"Erro Shopee: {e}")
        return []

# ---------------------------------------------------------------------------
# FORMATAR
# ---------------------------------------------------------------------------

def formatar(oferta):
    preco = f"R$ {oferta['preco']:.2f}".replace(".", ",")

    return (
        f"🔥 OFERTA\n\n"
        f"{oferta['nome'][:60]}\n\n"
        f"💰 {preco}\n\n"
        f"👉 {oferta['link']}"
    )

# ---------------------------------------------------------------------------
# ENVIO
# ---------------------------------------------------------------------------

async def enviar_mensagem(texto):
    try:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=texto
        )
    except Exception as e:
        log.error(f"Erro Telegram: {e}")

# ---------------------------------------------------------------------------
# JOB PRINCIPAL
# ---------------------------------------------------------------------------

async def job_ofertas():
    log.info("Buscando ofertas...")

    keyword = random.choice(SHOPEE_KEYWORDS)
    ofertas = buscar_ofertas_shopee(keyword)

    if not ofertas:
        log.info("Nenhuma oferta encontrada")
        return

    oferta = random.choice(ofertas)
    texto = formatar(oferta)

    await enviar_mensagem(texto)

# ---------------------------------------------------------------------------
# BOAS VINDAS
# ---------------------------------------------------------------------------

async def boas_vindas():
    await enviar_mensagem(
        f"🚀 Bot iniciado!\n\n"
        f"⏱ Ofertas a cada {INTERVAL_MINUTES} minutos"
    )

# ---------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------

def run_async(func):
    asyncio.run(func())

if __name__ == "__main__":
    log.info("Bot iniciado!")

    run_async(boas_vindas())
    run_async(job_ofertas())

    schedule.every(INTERVAL_MINUTES).minutes.do(lambda: run_async(job_ofertas))

    while True:
        schedule.run_pending()
        time.sleep(30)
