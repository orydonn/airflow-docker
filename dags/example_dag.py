# hello_world.py  ───────────────────────────────
from airflow import DAG
from airflow.decorators import task
import pendulum  # «правильные» timezone-aware даты
import json
from datetime import datetime, timezone
import time
from openai import OpenAI
import ccxt
from pathlib import Path

local_tz = "UTC"  # или "Europe/Berlin"
API_KEY = "удалил тот, который использовал. тут должен быть api ключ"
SYMBOL = "ETH/USDT"
TIMEFRAME = "1m"
LIMIT = 10
client = OpenAI(api_key=API_KEY)
EXCHANGE_CLASSES = {
    "binance": ccxt.binance,
    "kucoin": ccxt.kucoin,
    "okx": ccxt.okx,
}
ART_DIR = Path("/opt/airflow/mdfiles")
ART_DIR.mkdir(exist_ok=True)

ASSISTANT_NAME = "Data Analyst"
ASSISTANT_INSTRUCTIONS = (
    "Ты профессиональный аналитик данных. "
    "Ты хорошо разбираешься в том, как анализировать данные и создавать различные сравнительные таблицы "
    "Отвечай в формате Markdown, на русском языке."
)

def save_markdown(name: str, text: str) -> str:
    path = ART_DIR / name
    path.write_text(text + "\n", encoding="utf-8")
    return str(path)

def iso_timestamp(ms: int) -> str:
    return (
        datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
        .replace(second=0, microsecond=0)
        .isoformat()
    )


def fetch_candles(exchange, symbol, limit):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=limit)
    data = {}
    for ts, o, h, l, c, v in ohlcv[-limit:]:
        data[iso_timestamp(ts)] = {
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "volume": v,
        }
    return data


def create_assistant(model: str = "gpt-4o-mini") -> str:
    """Создаём ассистента каждый запуск (без сохранения ID)."""
    assistant = client.beta.assistants.create(
        name=ASSISTANT_NAME,
        instructions=ASSISTANT_INSTRUCTIONS,
        model=model,
    )
    return assistant.id


def ask_agent(prompt: str, model: str = "gpt-4o-mini") -> str:
    assistant_id = create_assistant(model)
    thread = client.beta.threads.create()

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt,
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
    )

    while run.status not in {"completed", "failed", "cancelled", "expired"}:
        time.sleep(2)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )

    if run.status != "completed":
        raise RuntimeError(f"Run finished with status: {run.status}")

    messages = client.beta.threads.messages.list(
        thread_id=thread.id,
        order="desc",
    )
    for msg in messages.data:
        if msg.role == "assistant":
            return msg.content[0].text.value.strip()

    raise RuntimeError("Ответ ассистента не найден")


with DAG(
        dag_id="ethPrice",
        description="Мини-пример TaskFlow DAG",
        start_date=pendulum.now(local_tz).subtract(days=1),
        schedule=None,
        catchup=False,
) as dag:
    @task
    def load_info() -> str:
        exchanges = {
            name: cls({"enableRateLimit": True}) for name, cls in EXCHANGE_CLASSES.items()
        }

        # Fetch candles per exchange
        per_exchange = {
            name: fetch_candles(ex, SYMBOL, LIMIT) for name, ex in exchanges.items()
        }

        # Merge by timestamp so that each minute key contains all three exchanges
        merged = {}
        timestamps = sorted({ts for ex_data in per_exchange.values() for ts in ex_data})

        for ts in timestamps:
            merged[ts] = {
                name: per_exchange[name].get(ts) for name in EXCHANGE_CLASSES
            }

        return json.dumps(merged, indent=2, ensure_ascii=False)


    @task
    def make_table(data="Нет данных") -> str:
        question = (
            f"Тебе нужно проанализировать данные: {data}. "
            "Финальный результат — таблица сравнения лучших курсов по площадкам. "
            "Столбцы: [Время, Лучшая цена открытия, Лучшая цена закрытия, "
            "Лучшая цена максимума, Лучшая цена минимума]. "
            "Формат ячейки: Цена (название платформы)."
            "ОТВЕТ ДОЛЖЕН СОДЕРЖАТЬ ТОЛЬКО ТАБЛИЦУ"
        )
        answer = ask_agent(question)
        save_markdown("table.md", answer)
        return answer

    @task
    def make_analysis(data="Нет данных") -> str:
        question = (
            f"Тебе нужно проанализировать данные: {data}. "
            "Финальный результат — анализ данных. Тебе нужно предоставить подробное описание, а также рекомендации для инвестора"
        )
        answer = ask_agent(question)
        save_markdown("analysis.md", answer)
        return answer


    @task
    def make_report(table_data="Нет таблицы", analysis_data="Нет анализа"):
        question = (
            f"Тебе нужно составить отчет о проделанной работе"
            "Финальный результат — отчет о том, что я сделал"
            f"Я создал таблицу с данными: {table_data}, а также сделал анализ: {analysis_data}"
            f"Тебе нужно составить отчет. Он должен быть сводной информацией о проделанной работе."
        )
        answer = ask_agent(question)
        save_markdown("report.md", answer)

    # ── зависимости ──
    load = load_info()
    table = make_table(load)
    analysis = make_analysis(load)
    load >> [table, analysis] >> make_report(table, analysis)
