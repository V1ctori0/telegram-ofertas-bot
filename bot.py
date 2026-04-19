import os
import time
import logging
import schedule
import asyncio
from telegram import Bot

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
# FUNÇÃO PRINCIPAL (AGORA CORRETA)
# ---------------------------------------------------------------------------

async def job_ofertas():
    log.info("Postando vitrine Shopee...")

    try:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=(
                "🔥 OFERTAS IMPERDÍVEIS NA SHOPEE\n\n"
                "🛍️ Roupas, tênis, perfumes e muito mais com desconto!\n\n"
                "👉 https://collshp.com/v1ctorio891\n\n"
                "⚡ Atualizado diariamente\n"
                "📲 Não perca!"
            )
        )
    except Exception as e:
        log.error(f"Erro ao enviar mensagem: {e}")

# ---------------------------------------------------------------------------
# BOAS-VINDAS
# ---------------------------------------------------------------------------

async def mensagem_boas_vindas():
    try:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=(
                "👋 Bot de Ofertas online!\n\n"
                "🔥 Vou postar ofertas automaticamente.\n"
                f"⏱ A cada {INTERVAL_MINUTES} minutos."
            )
        )
    except Exception as e:
        log.error(f"Erro boas-vindas: {e}")

# ---------------------------------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------------------------------

def run_job():
    asyncio.run(job_ofertas())

def run_boas_vindas():
    asyncio.run(mensagem_boas_vindas())

if __name__ == "__main__":
    log.info("Bot iniciado!")

    # roda imediatamente
    run_boas_vindas()
    run_job()

    # agenda
    schedule.every(INTERVAL_MINUTES).minutes.do(run_job)

    while True:
        schedule.run_pending()
        time.sleep(30)
