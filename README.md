# solanabot

Мультиагентный крипто-аналитик на CrewAI с Telegram-ботом. Собирает рыночные
данные по Solana (и другим монетам) через CoinGecko, прогоняет их через
цепочку агентов (данные → новости/sentiment → технический анализ → отчёт) и
хранит историю цен в SQLite.

## Структура

```
solanabot/
├── .env.example
├── requirements.txt
├── crypto_data.py     # CoinGecko API
├── agents.py           # CrewAI мультиагенты
├── storage.py           # SQLite история
├── telegram_bot.py     # Telegram-бот (команды)
└── main.py             # Точка входа
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

Токен Telegram: напиши `@BotFather` → `/newbot`.

## Запуск

```bash
python main.py
```

## Команды бота

- `/start` — приветствие и список команд
- `/sol` — текущая цена, изменение за 24ч, капитализация, объём
- `/report [coin]` — полный мультиагентный анализ (по умолчанию solana)
- `/history [SYMBOL]` — последние сохранённые записи цены (по умолчанию SOL)

## Примечания

- `/report` вызывает `crew.kickoff()`, который делает несколько LLM-вызовов
  подряд и требует `OPENAI_API_KEY`; ответ может занимать до минуты.
- `crypto_history.db` создаётся автоматически при первом сохранении цены.
