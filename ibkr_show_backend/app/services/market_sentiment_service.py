import logging
from functools import lru_cache

import requests
import yfinance as yf

from app.schemas.market_sentiment import (
    FearGreedRange,
    MarketSentimentResponse,
    VixRange,
)

logger = logging.getLogger(__name__)

VIX_RANGES = [
    ("< 12", 0, 12, "极度乐观", "谨慎追高,保持警觉", "#4ade80"),
    ("12—20", 12, 20, "正常区间", "常规定投,保持节奏", "#22c55e"),
    ("20—30", 20, 30, "恐惧上升", "加大定投,分批买入", "#fbbf24"),
    ("30—50", 30, 50, "市场恐慌", "加倍定投,逢低布局", "#f97316"),
    ("> 50", 50, 9999, "极度恐惧", "黄金机会,大胆抄底", "#ef4444"),
]

FEAR_GREED_RANGES = [
    ("0—24", 0, 25, "极度恐惧", "黄金机会,加倍买入", "#ef4444"),
    ("25—44", 25, 45, "恐惧", "加大定投,分批布局", "#f97316"),
    ("45—55", 45, 56, "中性", "常规定投,保持节奏", "#93c5fd"),
    ("56—75", 56, 76, "贪婪", "谨慎追高,控制仓位", "#fbbf24"),
    ("76—100", 76, 101, "极度贪婪", "警惕回调,部分止盈", "#22c55e"),
]


class MarketSentimentService:

    def get_sentiment(self) -> MarketSentimentResponse:
        vix_value = self._fetch_vix()
        fg_data = self._fetch_fear_greed()

        vix_ranges = self._build_vix_ranges(vix_value)
        fg_ranges = self._build_fear_greed_ranges(fg_data)

        vix_level = ""
        for r in vix_ranges:
            if r.is_current:
                vix_level = f"{r.sentiment} NORMAL" if r.sentiment == "正常区间" else r.sentiment

        fg_value = int(fg_data["value"]) if fg_data else None
        fg_level = ""
        for r in fg_ranges:
            if r.is_current:
                fg_level = f"{r.sentiment} GREED" if "贪" in r.sentiment else f"{r.sentiment} FEAR"

        return MarketSentimentResponse(
            vix_value=vix_value,
            vix_level=vix_level,
            vix_ranges=vix_ranges,
            fear_greed_value=fg_value,
            fear_greed_level=fg_level,
            fear_greed_ranges=fg_ranges,
        )

    def _fetch_vix(self) -> float | None:
        try:
            ticker = yf.Ticker("^VIX")
            df = ticker.history(period="3d")
            if df is not None and not df.empty:
                return float(df.iloc[-1]["Close"])
        except Exception as exc:
            logger.warning("获取 VIX 数据失败: %s", exc)
        return None

    def _fetch_fear_greed(self) -> dict | None:
        try:
            resp = requests.get(
                "https://api.alternative.me/fng/?limit=1",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            entries = data.get("data", [])
            if entries:
                return entries[0]
        except Exception as exc:
            logger.warning("获取 Fear & Greed 数据失败: %s", exc)
        return None

    @staticmethod
    def _build_vix_ranges(vix_value: float | None) -> list[VixRange]:
        ranges: list[VixRange] = []
        for label, lo, hi, sentiment, strategy, color in VIX_RANGES:
            is_current = vix_value is not None and lo <= vix_value < hi
            ranges.append(VixRange(
                label=label,
                sentiment=sentiment,
                strategy=strategy,
                color=color,
                is_current=is_current,
            ))
        return ranges

    @staticmethod
    def _build_fear_greed_ranges(fg_data: dict | None) -> list[FearGreedRange]:
        value = int(fg_data["value"]) if fg_data else None
        ranges: list[FearGreedRange] = []
        for label, lo, hi, sentiment, strategy, color in FEAR_GREED_RANGES:
            is_current = value is not None and lo <= value < hi
            ranges.append(FearGreedRange(
                label=label,
                sentiment=sentiment,
                strategy=strategy,
                color=color,
                is_current=is_current,
            ))
        return ranges
