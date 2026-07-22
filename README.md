# solanabot

Мультиагентный крипто-аналитик на CrewAI + ML с Telegram-ботом. Собирает рыночные данные по Solana (и другим монетам) через CoinGecko, прогоняет их через цепочку агентов, использует LSTM для предсказания цен, генерирует торговые сигналы и позволяет управлять портфелем.

## Структура

```
solanabot/
├── .env                 # Переменные окружения (не коммитить!)
├── .env.example         # Шаблон
├── requirements.txt     # Зависимости
├── crypto_data.py       # CoinGecko API
├── storage.py           # SQLite история цен
├── user_storage.py      # Многопользовательская система (портфель, alerts)
├── agents.py            # CrewAI мультиагенты с Tools
├── ml_model.py          # LSTM модель предсказания цен
├── signals.py           # Торговые сигналы (TA + ML)
├── telegram_bot.py      # Telegram бот со всеми командами
└── main.py              # Точка входа
```

## Установка

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Заполни `.env`:

```env
TELEGRAM_TOKEN=токен_от_BotFather
COINGECKO_API_KEY=
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

## Запуск

```bash
python main.py
```

## Команды бота

### 📊 Базовые данные
- `/start` — приветствие и список команд
- `/sol` — текущая цена, изменение за 24ч, капитализация, объём
- `/report [coin]` — полный мультиагентный анализ (по умолчанию solana)
- `/history [SYMBOL]` — последние сохранённые записи цены

### 🤖 ML & Сигналы
- `/predict [coin] [дней]` — предсказание цены на N дней (LSTM)
- `/signal [coin]` — торговый сигнал с confidence + Risk Management

### 💼 Портфель (мультипользовательский)
- `/portfolio add SOL 100 50000` — добавить позицию
- `/portfolio view` — просмотр портфеля с P&L
- `/portfolio close SOL 55000` — закрыть позицию

### 🔔 Alerts
- `/alert add SOL above 60` — alert если SOL > $60
- `/alert add BTC below 40000` — alert если BTC < $40000
- `/alert list` — все активные alerts

## Компоненты

### `ml_model.py` 🧠
- **LSTM нейросеть** для предсказания цен
- Нормализация данных (MinMaxScaler)
- Автосохранение моделей
- Fallback на линейный тренд (если TensorFlow не установлена)

### `signals.py` 🎯
- **SMA** (Simple Moving Average) — 7 и 14 дневные
- **RSI** (Relative Strength Index) — перекупленность/перепроданность
- **Волатильность** — стандартное отклонение
- **ML предсказание** — интеграция с ml_model.py
- **Confidence score** — оценка надёжности сигнала (0-100%)
- **Risk Management** — Stop Loss (-5%), Take Profit (+10%), R/R ratio

### `user_storage.py` 👥
- Многопользовательская система с отдельной БД `user_data.db`
- Сохранение портфеля каждого юзера
- Управление alerts
- История отчётов

### `agents.py` 🤖
- **4 CrewAI агента:**
  - Data Analyst — получает рыночные данные через Tool
  - News & Sentiment Analyst — анализирует тренды
  - Technical Analyst — TA через Tool доступа к истории
  - Senior Reporter — финальный отчёт с рекомендацией

### `crypto_data.py` 📡
- CoinGecko API для получения цен
- Market cap, volume, 24h change

### `storage.py` 💾
- SQLite история цен (`crypto_history.db`)
- Сохранение для TA анализа

## Примечания

- `/report` вызывает `crew.kickoff()`, который делает несколько LLM-вызовов подряд и требует `OPENAI_API_KEY`; ответ может занимать до минуты.
- `/predict` запускает обучение LSTM (требует `tensorflow`). Первый запуск медленнее.
- Каждый пользователь имеет отдельный портфель и alerts в `user_data.db`.
- `crypto_history.db` и `user_data.db` создаются автоматически.
- `models/` папка хранит обученные модели LSTM.

## Требования

- Python 3.8+
- OpenAI API ключ (для CrewAI)
- Telegram бот токен (от @BotFather)
- 2GB+ RAM (для TensorFlow)
