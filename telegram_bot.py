import asyncio
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from crypto_data import get_crypto_data
from storage import save_price, get_history
from ml_model import get_prediction
from signals import get_signal
from user_storage import (
    create_user, get_portfolio, add_portfolio_position, 
    close_position, add_alert, get_active_alerts, save_report
)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    create_user(telegram_id)
    
    await update.message.reply_text(
        "🚀 *Твой SOL & Crypto Multi-Agent готов!*\n\n"
        "*📊 Данные:*\n"
        "/sol — текущая цена\n"
        "/report [coin] — полный анализ\n"
        "/history [coin] — история цен\n\n"
        "*🤖 ML & Сигналы:*\n"
        "/predict [coin] [days] — предсказание на N дней\n"
        "/signal [coin] — торговый сигнал\n\n"
        "*💼 Портфель:*\n"
        "/portfolio add SOL 100 50000 — добавить позицию\n"
        "/portfolio view — просмотр портфеля\n"
        "/portfolio close SOL 55000 — закрыть позицию\n\n"
        "*🔔 Alerts:*\n"
        "/alert add SOL above 60 — alert если SOL > $60\n"
        "/alert list — все alerts",
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
    telegram_id = update.effective_user.id
    create_user(telegram_id)
    
    coin = context.args[0].lower() if context.args else "solana"
    await update.message.reply_text(f"🤖 Запускаю мультиагентов по {coin.upper()}... ⏳ (30-60 сек)")

    from agents import create_crew

    crew = create_crew(coin)
    try:
        result = await asyncio.to_thread(crew.kickoff)
        result_text = str(result)
        
        # Сохранить отчёт
        save_report(telegram_id, coin, result_text)
        
        # Split long messages
        if len(result_text) > 4000:
            for i in range(0, len(result_text), 4000):
                await update.message.reply_text(result_text[i:i+4000], parse_mode="Markdown")
        else:
            await update.message.reply_text(result_text, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка анализа: {str(e)[:200]}")


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coin = context.args[0].upper() if context.args else "SOL"
    hist = get_history(coin)
    if not hist:
        await update.message.reply_text("📜 История пуста.")
        return
    lines = [f"{row[0]} — ${row[2]:,.2f} ({row[3]:+.2f}%)" for row in hist]
    await update.message.reply_text("📜 Последние записи:\n" + "\n".join(lines))


async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("📈 Использование: /predict [coin] [дней]\nПример: /predict SOL 7")
        return
    
    coin = context.args[0].upper()
    days = int(context.args[1]) if len(context.args) > 1 else 7
    
    await update.message.reply_text(f"🤖 Обучаю модель для {coin}...")
    
    try:
        result = await asyncio.to_thread(get_prediction, coin, days)
        
        if "error" in result:
            await update.message.reply_text(f"⚠️ {result['error']}")
            return
        
        msg = f"*📊 Предсказание {coin}*\n"
        msg += f"Текущая цена: *${result['current_price']:,.2f}*\n\n"
        
        for i, (pred, change) in enumerate(zip(result['predictions'], result['change_percent']), 1):
            emoji = "📈" if change > 0 else "📉"
            msg += f"День {i}: ${pred:,.2f} ({change:+.2f}%) {emoji}\n"
        
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка: {str(e)[:200]}")


async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("🎯 Использование: /signal [coin]\nПример: /signal SOL")
        return
    
    coin = context.args[0].upper()
    
    try:
        result = await asyncio.to_thread(get_signal, coin, 1)
        
        if "error" in result:
            await update.message.reply_text(f"⚠️ {result['error']}")
            return
        
        ind = result['indicators']
        rm = result['risk_management']
        
        msg = f"*🎯 Торговый сигнал {coin}*\n\n"
        msg += f"Сигнал: *{result['signal']}*\n"
        msg += f"Confidence: *{result['confidence']}%*\n\n"
        msg += f"Текущая цена: ${result['current_price']:,.2f}\n"
        msg += f"Предсказание: ${result['predicted_price']:,.2f} ({result['ml_change_percent']:+.2f}%)\n\n"
        
        msg += f"*📊 Индикаторы:*\n"
        if ind['sma_short']:
            msg += f"SMA7: ${ind['sma_short']:,.2f}\n"
            msg += f"SMA14: ${ind['sma_long']:,.2f}\n"
        if ind['rsi']:
            msg += f"RSI: {ind['rsi']:.1f}\n"
        if ind['volatility']:
            msg += f"Волатильность: {ind['volatility']:.2f}%\n\n"
        
        msg += f"*⛑️ Risk Management:*\n"
        msg += f"Stop Loss: ${rm['stop_loss']:,.2f}\n"
        msg += f"Take Profit: ${rm['take_profit']:,.2f}\n"
        msg += f"R/R Ratio: {rm['risk_reward_ratio']:.2f}\n"
        
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка: {str(e)[:200]}")


async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    create_user(telegram_id)
    
    if not context.args:
        await update.message.reply_text("💼 Использование:\n/portfolio add [coin] [amount] [price]\n/portfolio view\n/portfolio close [coin] [price]")
        return
    
    action = context.args[0].lower()
    
    if action == "add":
        if len(context.args) < 4:
            await update.message.reply_text("❌ Использование: /portfolio add SOL 100 50000")
            return
        
        coin, amount, price = context.args[1], float(context.args[2]), float(context.args[3])
        add_portfolio_position(telegram_id, coin, amount, price)
        await update.message.reply_text(f"✅ Добавлена позиция: {amount} {coin} @ ${price:,.2f}")
    
    elif action == "view":
        portfolio = get_portfolio(telegram_id)
        if not portfolio:
            await update.message.reply_text("📜 Портфель пуст")
            return
        
        msg = "*💼 Ваш портфель:*\n\n"
        total_invested = 0
        
        for coin, amount, buy_price, buy_date in portfolio:
            current_data = get_crypto_data(coin.lower())
            current_price = current_data.get('price', buy_price)
            pnl = (current_price - buy_price) * amount
            pnl_percent = (current_price - buy_price) / buy_price * 100
            
            msg += f"*{coin}*: {amount} монет\n"
            msg += f"  Куплено: ${buy_price:,.2f}\n"
            msg += f"  Сейчас: ${current_price:,.2f}\n"
            msg += f"  P&L: ${pnl:,.2f} ({pnl_percent:+.2f}%)\n\n"
            
            total_invested += buy_price * amount
        
        await update.message.reply_text(msg, parse_mode="Markdown")
    
    elif action == "close":
        if len(context.args) < 3:
            await update.message.reply_text("❌ Использование: /portfolio close SOL 55000")
            return
        
        coin, sell_price = context.args[1], float(context.args[2])
        close_position(telegram_id, coin, sell_price)
        await update.message.reply_text(f"✅ Позиция {coin} закрыта @ ${sell_price:,.2f}")


async def alert_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    create_user(telegram_id)
    
    if not context.args:
        await update.message.reply_text("🔔 Использование:\n/alert add [coin] [above/below] [price]\n/alert list")
        return
    
    action = context.args[0].lower()
    
    if action == "add":
        if len(context.args) < 4:
            await update.message.reply_text("❌ Использование: /alert add SOL above 60")
            return
        
        coin, condition, threshold = context.args[1], context.args[2], float(context.args[3])
        add_alert(telegram_id, coin, condition, threshold)
        await update.message.reply_text(f"✅ Alert добавлен: {coin} {condition} ${threshold:,.2f}")
    
    elif action == "list":
        alerts = get_active_alerts(telegram_id)
        if not alerts:
            await update.message.reply_text("📜 Alerts пусто")
            return
        
        msg = "*🔔 Ваши alerts:*\n\n"
        for alert_id, coin, condition, threshold in alerts:
            msg += f"• {coin} {condition} ${threshold:,.2f}\n"
        
        await update.message.reply_text(msg, parse_mode="Markdown")


def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN не задан. Проверь .env")

    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sol", sol))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("predict", predict))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("alert", alert_cmd))
    
    print("✅ Бот запущен с ML функциями!")
    app.run_polling()


if __name__ == "__main__":
    main()
