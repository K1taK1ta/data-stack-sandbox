import os
import time
import numpy as np
import pandas as pd
from typing import Literal, Any, Optional
from statsmodels.tsa.seasonal import STL
from dotenv import load_dotenv
from wordstat_client import WordstatApiClient
from mcp.server.fastmcp import FastMCP
from postgres_db.orm import DataAccess
from postgres_db.models import RelatedKeywordsOrm, DynamicsKeywordsOrm, DecompositionKeywordsOrm
from logger import log

load_dotenv()
WORDSTAT_TOKEN = os.getenv('TOKEN')
client = WordstatApiClient(WORDSTAT_TOKEN)
mcp = FastMCP("Server")
rng = np.random.default_rng()

def get_prompt(tool_name: str) -> str:
    path = os.path.join("prompts", f"{tool_name}.md")

    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    except FileNotFoundError:
        return "Описание инструмента отсутствует."

def make_decomposition_stl(prepared_data: list[dict[str, Any]]) -> str:
    log.info("Запуск процесса STL-декомпозиции...")

    raw_data = prepared_data
    if not raw_data:
        log.warning("STL: Таблица динамики пуста. Нечего анализировать.")
        return "Данные не найдены"

    df = pd.DataFrame(raw_data)
    df['dynamics_date'] = pd.to_datetime(df['dynamics_date'])

    all_results = []
    unique_keywords = df['keyword'].unique()
    log.info(f"Найдено {len(unique_keywords)} уникальных фраз для анализа.")

    processed_count = 0
    skipped_count = 0

    for kw in unique_keywords:
        kw_df = df[df['keyword'] == kw].sort_values('dynamics_date')

        if len(kw_df) < 10:
            log.debug(f"Пропуск '{kw}': слишком мало данных ({len(kw_df)} точек).")
            skipped_count += 1
            continue

        try:
            kw_df = kw_df.set_index('dynamics_date')
            series = kw_df['impressions'].asfreq('W-MON').ffill()

            stl = STL(series, period=52, robust=True, seasonal=13)
            res = stl.fit()

            for date, val in series.items():
                all_results.append({
                    "keyword": kw,
                    "dynamics_date": date.date(),
                    "trend": float(res.trend[date]),
                    "seasonal": float(res.seasonal[date]),
                    "resid": float(res.resid[date])
                })

            processed_count += 1
            log.info(f"Обработано: '{kw}' ({len(series)} недель)")

        except Exception as e:
            log.error(f"Ошибка при декомпозиции фразы '{kw}': {e}")
            continue

    if all_results:
        log.info(f"Запись {len(all_results)} записей декомпозиции в базу данных...")
        DataAccess.upsert_table(DecompositionKeywordsOrm, data=all_results)

        summary = (f"STL декомпозиция завершена. "
                   f"Успешно: {processed_count}, Пропущено: {skipped_count}.")
        log.info(summary)
        return summary

    log.warning("STL: Ни одна фраза не прошла критерии анализа.")
    return "Недостаточно данных для анализа"

@mcp.tool()
def fetch_top_requests(phrases: list[str], region_name: str) -> str:

    region_id = client.get_region_id(region_name)
    for ph in phrases:
        data = client.fetch_top_requests(phrase=ph, region=[region_id])
        parent_keyword = data.get('requestPhrase')
        topRequests = data.get('topRequests', [])
        prepared_data = [
            {
                "parent_keyword": parent_keyword,
                "related_keyword": entry['phrase'],
                "impressions": entry['count'],
            }
            for entry in topRequests
        ]

        DataAccess.upsert_table(RelatedKeywordsOrm, data=prepared_data)

    log.info(
        "top_requests_processed",
        region=region_name,
        region_id=region_id,
        phrases_count=len(phrases),
        )

    return f"Успешно обработано фраз: {len(phrases)}"

@mcp.tool()
def fetch_dynamics(phrases: list[str], region_name: str) -> str:
    region_id = client.get_region_id(region_name)

    for ph in phrases:
        data = client.fetch_dynamics(
            phrase=ph,
            region=[region_id],
            fromDate="2023-01-02",
            toDate="2026-01-04",
            period='weekly'
        )

        keyword = data.get('requestPhrase')
        raw_dynamics = data.get('dynamics', [])
        prepared_data = [
            {
                "keyword": keyword,
                "impressions": entry['count'],
                "dynamics_date": entry['date']
            }
            for entry in raw_dynamics
        ]

        DataAccess.upsert_table(DynamicsKeywordsOrm, data=prepared_data)

    log.info(
            "dynamics_phrase_processed",
            phrases_count=len(phrases),
            region=region_name,
            )

    make_decomposition_stl(prepared_data)

    return (f"Успешно обработано фраз: {len(phrases)}). "
            f"Регион: {region_name}, Период: 2023-2025 год. "
            f"Примечание: Данные за последние 14 дней могут отсутствовать в API.")

@mcp.tool()
def event_log_generator(
    scenario: Literal["normal", "burst", "sparse"] = "normal",
    level: Literal["debug", "info", "warning", "error", "critical"] = "info",
    intensity: int = 50,
    count: int = 500
) -> None:

    avg_interval = 1.0 / intensity
    log.info(f"Запуск сценария '{scenario}': {count} событий, база {intensity} EPS")

    for i in range(1, count + 1):
        try:
            if scenario == "burst":
                current_interval = avg_interval / 5 if rng.random() > 0.8 else avg_interval * 2
            elif scenario == "sparse":
                current_interval = rng.uniform(avg_interval * 1.5, avg_interval * 3.0)
            else:
                current_interval = rng.exponential(scale=avg_interval)

            log_func = getattr(log, level.lower(), log.info)
            log_func(f"[{i}/{count}] Событие зафиксировано [Сценарий: {scenario}]")

            if i < count:
                time.sleep(current_interval)

        except KeyboardInterrupt:
            log.warning("\nГенерация прервана пользователем.")
            break

    log.info("Генерация успешно завершена.")


fetch_top_requests.__doc__ = get_prompt("fetch_top_requests")
fetch_dynamics.__doc__ = get_prompt("fetch_dynamics")
event_log_generator.__doc__ = get_prompt("event_log_generator")