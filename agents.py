import os
from crewai import Agent, Task, Crew, Tool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from crypto_data import get_crypto_data
from storage import get_history

load_dotenv()
llm = ChatOpenAI(model=os.getenv("LLM_MODEL", "gpt-4o-mini"), temperature=0.7)

# Tools for agents
def fetch_current_price(coin: str) -> str:
    """Fetch current price and market data for a cryptocurrency"""
    data = get_crypto_data(coin)
    if "error" in data:
        return f"Error: {data['error']}"
    return f"""
Current {data['coin']} ({data['symbol']}):
- Price: ${data['price']:,.2f}
- 24h Change: {data['change_24h']:.2f}%
- Market Cap: ${data['market_cap']:,.0f}
- Volume 24h: ${data['volume_24h']:,.0f}
"""

def fetch_price_history(coin: str) -> str:
    """Fetch price history for technical analysis"""
    history = get_history(coin, limit=20)
    if not history:
        return f"No history found for {coin}"
    lines = [f"{row[0]}: ${row[2]:,.2f} ({row[3]:+.2f}%)" for row in history]
    return "\n".join(lines)

# Create tools
price_tool = Tool(
    name="get_current_price",
    func=fetch_current_price,
    description="Get current price, market cap, volume for a cryptocurrency"
)

history_tool = Tool(
    name="get_price_history",
    func=fetch_price_history,
    description="Get price history for technical analysis"
)

data_agent = Agent(
    role="Data Analyst",
    goal="Собирать точные рыночные данные по крипте",
    backstory="Эксперт по CoinGecko и on-chain метрикам",
    verbose=True,
    llm=llm,
    tools=[price_tool],
)

news_agent = Agent(
    role="News & Sentiment Analyst",
    goal="Анализировать новости и настроение рынка",
    backstory="Специалист по sentiment analysis и крипто-новостям. Анализирует рыночные тренды и настроение.",
    verbose=True,
    llm=llm,
)

tech_agent = Agent(
    role="Technical Analyst",
    goal="Делать технический анализ и прогноз",
    backstory="Профессиональный трейдер с TA. Использует паттерны и уровни поддержки/сопротивления.",
    verbose=True,
    llm=llm,
    tools=[history_tool],
)

reporter = Agent(
    role="Senior Crypto Reporter",
    goal="Собирать всё в понятный отчёт и давать рекомендации",
    backstory="Главный аналитик с опытом 10+ лет. Даёт чёткую рекомендацию: BUY/HOLD/SELL",
    verbose=True,
    llm=llm,
)


def create_crew(coin="solana"):
    task1 = Task(
        description=f"Получи актуальные рыночные данные по {coin} используя инструмент get_current_price",
        agent=data_agent,
        expected_output="JSON с ценой, изменением 24h, капитализацией и объёмом",
    )
    task2 = Task(
        description=f"На основе рыночных данных {coin} проанализируй тренды и настроение рынка. Какие факторы влияют на цену?",
        agent=news_agent,
        expected_output="Анализ текущего настроения рынка и основные движущие факторы",
    )
    task3 = Task(
        description=f"Получи историю цен {coin} и сделай технический анализ. Определи ключевые уровни поддержки/сопротивления и паттерны",
        agent=tech_agent,
        expected_output="Техническая рекомендация с анализом уровней и паттернов",
    )
    task4 = Task(
        description="Собери всё в финальный отчёт. Используй информацию из всех предыдущих задач. Дай финальную рекомендацию: BUY/HOLD/SELL с обоснованием.",
        agent=reporter,
        expected_output="Полный markdown отчёт с финальной рекомендацией",
        context=[task1, task2, task3],
    )

    return Crew(
        agents=[data_agent, news_agent, tech_agent, reporter],
        tasks=[task1, task2, task3, task4],
        verbose=True,
    )
