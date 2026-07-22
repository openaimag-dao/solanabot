import os

from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(model=os.getenv("LLM_MODEL", "gpt-4o-mini"), temperature=0.7)

data_agent = Agent(
    role="Data Analyst",
    goal="Собирать точные рыночные данные по крипте",
    backstory="Эксперт по CoinGecko и on-chain метрикам",
    verbose=True,
    llm=llm,
)

news_agent = Agent(
    role="News & Sentiment Analyst",
    goal="Анализировать новости и настроение рынка",
    backstory="Специалист по sentiment analysis и крипто-новостям",
    verbose=True,
    llm=llm,
)

tech_agent = Agent(
    role="Technical Analyst",
    goal="Делать технический анализ и прогноз",
    backstory="Профессиональный трейдер с TA",
    verbose=True,
    llm=llm,
)

reporter = Agent(
    role="Senior Crypto Reporter",
    goal="Собирать всё в понятный отчёт и давать рекомендации",
    backstory="Главный аналитик с опытом 10+ лет",
    verbose=True,
    llm=llm,
)


def create_crew(coin="solana"):
    task1 = Task(
        description=f"Получи актуальные данные по {coin}",
        agent=data_agent,
        expected_output="JSON с данными",
    )
    task2 = Task(
        description=f"Найди последние новости и sentiment по {coin}",
        agent=news_agent,
        expected_output="Анализ новостей",
    )
    task3 = Task(
        description=f"Сделай технический анализ {coin}",
        agent=tech_agent,
        expected_output="TA выводы",
    )
    task4 = Task(
        description="Собери всё в финальный отчёт с рекомендацией (BUY/HOLD/SELL)",
        agent=reporter,
        expected_output="Полный markdown отчёт",
        context=[task1, task2, task3],
    )

    return Crew(
        agents=[data_agent, news_agent, tech_agent, reporter],
        tasks=[task1, task2, task3, task4],
        verbose=True,
    )
