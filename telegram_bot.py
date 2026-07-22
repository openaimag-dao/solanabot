import asyncio
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from crypto_data import get_crypto_data
from storage import save_price, get_history

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 *Твой SOL & Crypto Multi-Agent* готов!\n\n"
        "/sol — данные\n"
        "/report SOL — полный анализ\n"
        "/history — история",
        parse_mode="Markdown",
    )


async def sol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_crypto_data("solana")
    if "error" in data:
        await update.message.reply_text(f"⚠️ Ошибка: {data['error']}")
        return
    save_price(data)
    msg = (
        f"*{data['coin']} ({data['symbol']})*\n"
        f"💰 Цена: *${data['price']:,.2f}*\n"
        f"24ч: *{data['change_24h']:.2f}%*\n"
        f"📊 Cap: ${data['market_cap']:,.0f}\n"
        f"🔄 Volume: ${data['volume_24h']:,.0f}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coin = context.args[0].lower() if context.args else "solana"
    await update.message.reply_text(f"🤖 Запускаю мультиагентов по {coin.upper()}...")

    # crew.kickoff() is a blocking, synchronous call — run it off the event
    # loop thread so the bot keeps responding to other updates meanwhile.
    from agents import create_crew

    crew = create_crew(coin)
    try:
        result = await asyncio.to_thread(crew.kickoff)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка анализа: {e}")
        return
    await update.message.reply_text(str(result), parse_mode="Markdown")


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coin = context.args[0].upper() if context.args else "SOL"
    hist = get_history(coin)
    if not hist:
        await update.message.reply_text("📜 История пуста.")
        return
    lines = [f"{row[0]} — ${row[2]:,.2f} ({row[3]:+.2f}%)" for row in hist]
    await update.message.reply_text("📜 Последние записи:\n" + "\n".join(lines))


def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN не задан. Проверь .env")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sol", sol))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("history", history))
    print("✅ Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
