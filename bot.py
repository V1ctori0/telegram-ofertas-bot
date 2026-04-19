import os
import time
import random
import logging
import asyncio
import requests
import schedule
from telegram import Bot
 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)
 
BOT_TOKEN        = os.environ["BOT_TOKEN"]
CHANNEL_ID       = os.environ["CHANNEL_ID"]
INTERVAL_MINUTES = int(os.environ.get("INTERVAL_MINUTES", "15"))
LINK_AFILIADO    = os.environ.get("LINK_AFILIADO", "https://collshp.com/v1ctorio891")
 
bot = Bot(token=BOT_TOKEN)
 
# ---------------------------------------------------------------------------
# CATEGORIAS E KEYWORDS
# ---------------------------------------------------------------------------
 
CATEGORIAS = {
    "calcados": {
        "emoji": "👟",
        "nome": "CALCADOS",
        "keywords": [
            "tenis masculino",
            "tenis nike masculino",
            "tenis adidas masculino",
            "tenis vans masculino",
            "tenis new balance masculino",
            "tenis puma masculino",
            "tenis para academia",
            "sapato masculino social",
            "sapatenis masculino",
            "bota masculina",
            "chinelo masculino",
            "sandalia masculina",
            "tenis feminino",
            "tenis nike feminino",
            "sapato feminino",
            "scarpin feminino",
            "tenis infantil",
        ],
    },
    "roupas": {
        "emoji": "👕",
        "nome": "ROUPAS",
        "keywords": [
            "camiseta masculina",
            "camisa polo masculina",
            "calca jeans masculina",
            "bermuda masculina",
            "moletom masculino",
            "conjunto moletom",
            "camiseta feminina",
            "blusa feminina",
            "vestido feminino",
            "calca feminina",
            "conjunto feminino",
            "pijama adulto",
            "roupa academia masculina",
            "roupa academia feminina",
            "uniforme escolar",
        ],
    },
    "acessorios": {
        "emoji": "⌚",
        "nome": "ACESSORIOS",
        "keywords": [
            "relogio masculino",
            "smartwatch",
            "oculos de sol masculino",
            "oculos de sol feminino",
            "mochila masculina",
            "mochila escolar",
            "carteira masculina",
            "cinto masculino",
            "bone masculino",
            "perfume masculino",
            "perfume feminino",
            "colar feminino",
            "pulseira feminina",
            "brinco feminino",
            "mala de viagem",
        ],
    },
    "tecnologia": {
        "emoji": "📱",
        "nome": "TECNOLOGIA",
        "keywords": [
            "fone de ouvido bluetooth",
            "fone sem fio",
            "carregador rapido",
            "cabo usb tipo c",
            "suporte celular carro",
            "capa celular",
            "power bank",
            "caixa de som bluetooth",
            "mouse sem fio",
            "teclado bluetooth",
            "hub usb",
            "lampada led inteligente",
            "webcam full hd",
            "headset gamer",
            "suporte notebook",
        ],
    },
}
 
# Filas por categoria — embaralha e percorre em ciclo
_filas: dict = {cat: [] for cat in CATEGORIAS}
_ordem_cats: list = []
 
 
def proxima_keyword(categoria: str) -> str:
    if not _filas[categoria]:
        _filas[categoria] = CATEGORIAS[categoria]["keywords"].copy()
        random.shuffle(_filas[categoria])
        log.info(f"Fila '{categoria}' recarregada.")
    return _filas[categoria].pop()
 
 
def proxima_categoria() -> str:
    global _ordem_cats
    if not _ordem_cats:
        # cada categoria aparece 2x antes de repetir, em ordem aleatoria
        _ordem_cats = list(CATEGORIAS.keys()) * 2
        random.shuffle(_ordem_cats)
    return _ordem_cats.pop()
 
 
# ---------------------------------------------------------------------------
# HEADERS SHOPEE
# ---------------------------------------------------------------------------
 
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Referer": "https://shopee.com.br/",
}
 
 
# ---------------------------------------------------------------------------
# BUSCA NA SHOPEE — API publica, sem chave
# Ordena por mais vendidos, filtra so produtos com estoque e desconto
# ---------------------------------------------------------------------------
 
def buscar_shopee(keyword: str) -> list:
    url = "https://shopee.com.br/api/v4/search/search_items"
    params = {
        "by": "sales",
        "keyword": keyword,
        "limit": 30,
        "newest": 0,
        "order": "desc",
        "page_type": "search",
        "scenario": "PAGE_GLOBAL_SEARCH",
        "version": 2,
    }
    for tentativa in range(3):
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=12)
            if resp.status_code != 200:
                log.warning(f"Shopee {resp.status_code} — tentativa {tentativa + 1}")
                time.sleep(3)
                continue
 
            itens = resp.json().get("items") or []
            produtos = []
 
            for item in itens:
                info     = item.get("item_basic") or {}
                nome     = info.get("name", "").strip()
                imagem   = info.get("image", "")
                estoque  = info.get("stock", 1)
                desconto = info.get("raw_discount", 0)
                shopid   = info.get("shopid", "")
                itemid   = info.get("itemid", "")
                vendas   = info.get("sold", 0)
                rating   = round((info.get("item_rating") or {}).get("rating_star", 0), 1)
                preco_c  = info.get("price", 0)
                orig_c   = info.get("price_before_discount", 0)
 
                # descarta sem nome, sem imagem, sem estoque ou desconto irrelevante
                if not nome or not imagem or estoque == 0 or desconto < 5:
                    continue
 
                preco_atual = preco_c / 100000
                preco_orig  = orig_c / 100000 if orig_c > preco_c else None
 
                if preco_atual <= 0:
                    continue
 
                link = (
                    f"https://shopee.com.br/product/{shopid}/{itemid}"
                    f"?utm_source=telegram&utm_medium=afiliado"
                    f"&aff_link={LINK_AFILIADO}"
                )
                imagem_url = f"https://cf.shopee.com.br/file/{imagem}_tn"
 
                produtos.append({
                    "nome":        nome,
                    "preco_atual": preco_atual,
                    "preco_orig":  preco_orig,
                    "desconto":    desconto,
                    "vendas":      vendas,
                    "rating":      rating,
                    "link":        link,
                    "imagem":      imagem_url,
                })
 
            return produtos
 
        except Exception as e:
            log.error(f"Erro rede: {e} — tentativa {tentativa + 1}")
            time.sleep(5)
 
    return []
 
 
def melhor_produto(produtos: list) -> dict | None:
    if not produtos:
        return None
    # pontuacao: desconto + vendas + rating
    def score(p):
        return (p["desconto"] * 2) + (min(p["vendas"], 5000) / 100) + (p["rating"] * 10)
    return max(produtos, key=score)
 
 
# ---------------------------------------------------------------------------
# FORMATACAO DA MENSAGEM
# ---------------------------------------------------------------------------
 
def brl(valor: float) -> str:
    return "R$ {:,.2f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".")
 
 
def formatar(produto: dict, categoria: str) -> str:
    cfg   = CATEGORIAS[categoria]
    emoji = cfg["emoji"]
    nome  = cfg["nome"]
 
    titulo = produto["nome"][:55] + ("..." if len(produto["nome"]) > 55 else "")
    preco  = brl(produto["preco_atual"])
 
    msg = f"{emoji} {nome} - OFERTA SHOPEE {emoji}\n\n"
    msg += f"🏷️ {titulo}\n\n"
    msg += f"💰 POR APENAS {preco}\n"
 
    if produto["preco_orig"]:
        msg += f"🔖 De {brl(produto['preco_orig'])} → {produto['desconto']}% OFF\n"
 
    if produto["rating"] >= 4.0:
        msg += f"⭐ {produto['rating']}/5\n"
 
    if produto["vendas"] > 0:
        v = "{:,}".format(produto["vendas"]).replace(",", ".")
        msg += f"📦 {v} pessoas compraram\n"
 
    msg += "\n✅ Frete grátis em pedidos elegíveis\n"
    msg += "⏰ Oferta por tempo limitado\n\n"
    msg += f"👉 COMPRAR AGORA: {produto['link']}\n\n"
    msg += "🔔 Ative as notificações para não perder nenhuma oferta!"
 
    return msg
 
 
# ---------------------------------------------------------------------------
# ENVIO AO CANAL
# ---------------------------------------------------------------------------
 
async def enviar(produto: dict, categoria: str):
    texto = formatar(produto, categoria)
    try:
        # tenta com foto
        await bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=produto["imagem"],
            caption=texto,
        )
        log.info(f"[{categoria.upper()}] Enviado: {produto['nome'][:45]}")
    except Exception as e:
        log.warning(f"Foto falhou ({e}), enviando so texto...")
        try:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=texto,
                disable_web_page_preview=False,
            )
        except Exception as e2:
            log.error(f"Falha total no envio: {e2}")
 
 
# ---------------------------------------------------------------------------
# JOB PRINCIPAL
# ---------------------------------------------------------------------------
 
async def job_ofertas():
    categoria = proxima_categoria()
    keyword   = proxima_keyword(categoria)
    log.info(f"Buscando [{categoria}] -> '{keyword}'")
 
    produtos = buscar_shopee(keyword)
    produto  = melhor_produto(produtos)
 
    if not produto:
        log.warning(f"Nenhum produto valido para '{keyword}'. Pulando.")
        return
 
    await enviar(produto, categoria)
 
 
# ---------------------------------------------------------------------------
# BOAS-VINDAS
# ---------------------------------------------------------------------------
 
async def boas_vindas():
    cats = "\n".join(
        f"{v['emoji']} {v['nome']}" for v in CATEGORIAS.values()
    )
    try:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=(
                f"👋 Bot de Ofertas Shopee online!\n\n"
                f"🔥 Vou postar os produtos mais vendidos e com melhor desconto!\n\n"
                f"📦 Categorias:\n{cats}\n\n"
                f"⏱ Nova oferta a cada {INTERVAL_MINUTES} minutos\n\n"
                f"🔔 Ative as notificações e não perca nada!"
            ),
        )
    except Exception as e:
        log.error(f"Erro boas-vindas: {e}")
 
 
# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
 
def run_job():
    asyncio.run(job_ofertas())
 
def run_boas_vindas():
    asyncio.run(boas_vindas())
 
if __name__ == "__main__":
    log.info("Bot iniciado!")
    run_boas_vindas()
    run_job()
 
    schedule.every(INTERVAL_MINUTES).minutes.do(run_job)
 
    while True:
        schedule.run_pending()
        time.sleep(30)
