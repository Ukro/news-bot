import asyncio, aiosqlite, feedparser, hashlib, json, httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# BOT_TOKEN БУДЕ З ENV (не в коді для безпеки)
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не налаштовано! Додайте в Environment Variables на Render.")

DB_NAME = "users.db"

# ─── УКРАЇНСЬКІ ФІДИ (Holosameryky + Свобода + BBC) ───────────────────
TOPICS = {
    "Політика": [
        "https://www.holosameryky.com/api/zroyml-vomx-tpeokt_",
        "https://www.holosameryky.com/api/zbirorl-vomx-tpeqjooq",
        "https://www.holosameryky.com/api/zmkbqyl-vomx-tpeypooy",
        "https://feeds.bbci.co.uk/ukrainian/politics/rss.xml",
        "https://www.radiosvoboda.org/api/zrqitl-vomx-tpeoumq",
    ],
    "Війна": [
        "https://www.holosameryky.com/api/z_ygqil-vomx-tpevrbqp",
        "https://www.holosameryky.com/api/zioyvl-vomx-tpemktt",
        "https://www.holosameryky.com/api/z_ovqyl-vomx-tpevkuqv",
        "https://feeds.bbci.co.uk/ukrainian/war/rss.xml",
        "https://www.radiosvoboda.org/api/zrqitl-vomx-tpeoumq",
    ],
    "Наука": [
        "https://www.holosameryky.com/api/ztmvqpl-vomx-tpek-uqp",
        "https://www.holosameryky.com/api/zvjkqvl-vomx-tpeu_-qv",
        "https://www.holosameryky.com/api/zbupqql-vomx-tpeqpyqo",
        "https://feeds.bbci.co.uk/ukrainian/science/rss.xml",
        "https://www.radiosvoboda.org/api/zrqitl-vomx-tpeoumq",
    ],
    "Спорт": [
        "https://www.holosameryky.com/api/z-oyrl-vomx-tpergtq",
        "https://www.holosameryky.com/api/ztuyqvl-vomx-tpekiuqt",
        "https://www.holosameryky.com/api/zpkbq_l-vomx-tpe_poo_",
        "https://feeds.bbci.co.uk/ukrainian/sport/rss.xml",
    ],
    "Економіка": [
        "https://www.holosameryky.com/api/z-vmqtl-vomx-tperovqr",
        "https://www.holosameryky.com/api/zmu-qpl-vomx-tpeyiqo_",
        "https://www.holosameryky.com/api/z_u-qml-vomx-tpeviqoy",
        "https://feeds.bbci.co.uk/ukrainian/business/rss.xml",
        "https://www.radiosvoboda.org/api/zrqitl-vomx-tpeoumq",
    ],
    "Культура": [
        "https://www.holosameryky.com/api/z_kbqvl-vomx-tpevpoov",
        "https://www.holosameryky.com/api/zqoy_l-vomx-tpeikty",
        "https://www.holosameryky.com/api/zpoytl-vomx-tpe_ktr",
        "https://feeds.bbci.co.uk/ukrainian/culture/rss.xml",
        "https://www.radiosvoboda.org/api/zrqitl-vomx-tpeoumq",
    ],
    "Суспільство": [
        "https://www.holosameryky.com/api/zyovqvl-vomx-tpetkuqt",
        "https://www.holosameryky.com/api/zvoypl-vomx-tpeuktm",
        "https://www.holosameryky.com/api/zggvqql-vomx-tpe-mkqi",
        "https://www.holosameryky.com/api/zvuyqyl-vomx-tpeuiuqv",
        "https://www.radiosvoboda.org/api/zrqitl-vomx-tpeoumq",
    ],
    "Міжнародне": [
        "https://www.holosameryky.com/api/z_krqql-vomx-tpevpiqo",
        "https://www.holosameryky.com/api/zjumqil-vomx-tpebivqm",
        "https://www.holosameryky.com/api/zkgkqpl-vomx-tpejm-qp",
        "https://www.holosameryky.com/api/zbubrl-vomx-tpeqpoqr",
        "https://www.holosameryky.com/api/zbbyqpl-vomx-tpeqtuqm",
    ],
    "США": [
        "https://www.holosameryky.com/api/zgoyvl-vomx-tpe-ktt",
        "https://www.holosameryky.com/api/z---qml-vomx-tpervqo_",
        "https://www.holosameryky.com/api/zkoyyl-vomx-tpejktv",
        "https://www.holosameryky.com/api/zooyyl-vomx-tpepktv",
        "https://www.holosameryky.com/api/z_oyol-vomx-tpevkto",
    ],
    "Європа": [
        "https://www.holosameryky.com/api/zuovqql-vomx-tpegkuqo",
        "https://www.holosameryky.com/api/ztoyml-vomx-tpekkt_",
        "https://www.holosameryky.com/api/zgmmqil-vomx-tpe--yqm",
        "https://www.holosameryky.com/api/zokyqvl-vomx-tpeppuqt",
        "https://www.radiosvoboda.org/api/zrqitl-vomx-tpeoumq",
    ],
}

# ─── RFI (французькою → укр. через LibreTranslate) ───────────────────
RFI_FEEDS = {
    "Міжнародне": "https://www.rfi.fr/fr/monde/rss",
    "Європа": "https://www.rfi.fr/fr/europe/rss",
    "Політика": "https://www.rfi.fr/fr/politique/rss",
    "Економіка": "https://www.rfi.fr/fr/eco/rss",
    "Культура": "https://www.rfi.fr/fr/culture/rss",
}

# ─── КЛЮЧОВІ СЛОВА ───────────────────────────────────────────────────
KEYWORDS = {
    "Політика": ["зеленський","рада","вибори","кабмін","політика"],
    "Війна": ["зсу","фронт","обстріл","атака","війна"],
    "Наука": ["дослідження","nasa","ai","технології","наука"],
    "Спорт": ["футбол","матч","олімпіада","спорт"],
    "Економіка": ["ввп","інфляція","бізнес","криза","економіка"],
    "Культура": ["фільм","книга","виставка","музика","культура"],
    "Суспільство": ["суспільство","права","освіта","здоров'я"],
    "Міжнародне": ["сша","європа","оон","міжнародне"],
    "США": ["байден","конгрес","америка","сша"],
    "Європа": ["єс","нато","європа","брюссель"],
}

# ─── ПЕРЕКЛАД (LibreTranslate) ───────────────────────────────────────
async def translate_fr_to_uk(text: str) -> str:
    if not text.strip(): return text
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://libretranslate.de/translate",
                json={"q": text, "source": "fr", "target": "uk", "format": "text"},
                timeout=10
            )
            return resp.json()["translatedText"]
    except:
        return text

# ─── БАЗА ДАНИХ ─────────────────────────────────────────────────────
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, topics TEXT)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS posted (hash TEXT PRIMARY KEY)""")
        await db.commit()

# ─── КЛАВІАТУРА ─────────────────────────────────────────────────────
def get_topics_keyboard(selected=None):
    all_topics = {**TOPICS, **RFI_FEEDS}
    if selected is None: selected = []
    kb = []
    for t in all_topics:
        emoji = "✅" if t in selected else "⬜"
        kb.append([InlineKeyboardButton(f"{emoji} {t}", callback_data=f"toggle_{t}")])
    kb.append([InlineKeyboardButton("Готово ✅", callback_data="done")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ─── БОТ ───────────────────────────────────────────────────────────
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer("Обери теми новин (вкл. RFI українською):", reply_markup=get_topics_keyboard())

@dp.callback_query(lambda c: c.data.startswith("toggle_"))
async def toggle(cb: types.CallbackQuery):
    user_id = cb.from_user.id
    topic = cb.data.split("_",1)[1]
    async with aiosqlite.connect(DB_NAME) as db:
        row = await (await db.execute("SELECT topics FROM users WHERE user_id=?",(user_id,))).fetchone()
        topics = json.loads(row[0]) if row else []
        topics = [t for t in topics if t!=topic] if topic in topics else topics+[topic]
        await db.execute("INSERT OR REPLACE INTO users(user_id,topics) VALUES(?,?)",(user_id,json.dumps(topics)))
        await db.commit()
    await cb.message.edit_reply_markup(reply_markup=get_topics_keyboard(topics))
    await cb.answer()

@dp.callback_query(lambda c: c.data=="done")
async def done(cb: types.CallbackQuery):
    await cb.message.edit_text("Готово! Новини приходитимуть кожні 30 хв.")
    await cb.answer()

# ─── ПАРСИНГ ───────────────────────────────────────────────────────
async def parse_and_send(rss_url, topic, users, translate=False):
    try:
        feed = feedparser.parse(rss_url)
        if not feed.entries: return
        for e in feed.entries[:2]:
            title = e.title
            link = e.link
            summary = (e.summary or "")[:300]
            if translate:
                title = await translate_fr_to_uk(title)
                summary = await translate_fr_to_uk(summary)
            text = f"{title} {summary}".lower()
            if not any(w in text for w in KEYWORDS.get(topic,[])): continue
            h = hashlib.md5(f"{topic}_{link}".encode()).hexdigest()
            async with aiosqlite.connect(DB_NAME) as db:
                if await (await db.execute("SELECT 1 FROM posted WHERE hash=?",(h,))).fetchone(): continue
                msg = f"*{title}*\n\n{summary}...\n\n[Читати →]({link})"
                if translate: msg += "\n\n_Перекладено з RFI (Франція)_"
                for uid, tjson in users:
                    if topic in json.loads(tjson):
                        try: await bot.send_message(uid, msg, parse_mode="Markdown", disable_web_page_preview=True)
                        except: pass
                await db.execute("INSERT INTO posted(hash) VALUES(?)",(h,))
                await db.commit()
            await asyncio.sleep(1)
    except Exception as ex: print(f"ERR {rss_url}: {ex}")

async def send_personalized_news():
    async with aiosqlite.connect(DB_NAME) as db:
        users = await (await db.execute("SELECT user_id,topics FROM users")).fetchall()
    for topic, feeds in TOPICS.items():
        for url in feeds:
            await parse_and_send(url, topic, users, translate=False)
    for topic, url in RFI_FEEDS.items():
        await parse_and_send(url, topic, users, translate=True)

async def scheduler():
    while True:
        await send_personalized_news()
        await asyncio.sleep(1800)

# ─── ЗАПУСК ───────────────────────────────────────────────────────
async def main():
    await init_db()
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)

if __name__ == "__main__":

    asyncio.run(main())
