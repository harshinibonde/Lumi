"""
Lightweight behavioral summaries from logged chat turns (no ML).
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any


def _parse_ts(s: str) -> datetime | None:
    if not s or not isinstance(s, str):
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:19], fmt.replace("T", " ")[: len(fmt)])
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def build_behavioral_insights(series: list[dict[str, Any]]) -> dict[str, Any]:
    chat = [r for r in series if r.get("task_type") == "chat_turn"]
    if not chat:
        return {
            "chat_turns_7d": 0,
            "chat_turns_prev_7d": 0,
            "latency_trend": "unknown",
            "avg_latency_7d": None,
            "avg_latency_prev_7d": None,
            "accuracy_trend": "unknown",
            "avg_accuracy_7d": None,
            "avg_accuracy_prev_7d": None,
            "active_days_30d": 0,
            "hints_avg_7d": None,
        }

    now = datetime.utcnow()
    cut_7 = now - timedelta(days=7)
    cut_14 = now - timedelta(days=14)

    last7: list[dict] = []
    prev7: list[dict] = []
    for r in chat:
        ts = _parse_ts(str(r.get("session_timestamp", "")))
        if ts is None:
            continue
        if ts >= cut_7:
            last7.append(r)
        elif cut_14 <= ts < cut_7:
            prev7.append(r)

    def avg_lat(rows: list[dict]) -> float | None:
        xs = [float(r["latency"]) for r in rows if r.get("latency") is not None]
        return round(sum(xs) / len(xs), 3) if xs else None

    def avg_acc(rows: list[dict]) -> float | None:
        xs = [float(r["accuracy"]) for r in rows if r.get("accuracy") is not None]
        return round(sum(xs) / len(xs), 3) if xs else None

    def avg_hints(rows: list[dict]) -> float | None:
        xs = [int(r["hints_used"] or 0) for r in rows]
        return round(sum(xs) / len(xs), 2) if xs else None

    al7, al0 = avg_lat(last7), avg_lat(prev7)
    aa7, aa0 = avg_acc(last7), avg_acc(prev7)

    def trend(cur: float | None, prev: float | None, lower_is_better: bool) -> str:
        if cur is None or prev is None:
            return "stable"
        if abs(cur - prev) < 0.05 * max(prev, 0.01):
            return "stable"
        improved = cur < prev if lower_is_better else cur > prev
        return "improving" if improved else "worsening"

    days: set[str] = set()
    cut_30 = now - timedelta(days=30)
    for r in chat:
        ts = _parse_ts(str(r.get("session_timestamp", "")))
        if ts and ts >= cut_30:
            days.add(ts.strftime("%Y-%m-%d"))

    return {
        "chat_turns_7d": len(last7),
        "chat_turns_prev_7d": len(prev7),
        "latency_trend": trend(al7, al0, lower_is_better=True),
        "avg_latency_7d": al7,
        "avg_latency_prev_7d": al0,
        "accuracy_trend": trend(aa7, aa0, lower_is_better=False),
        "avg_accuracy_7d": aa7,
        "avg_accuracy_prev_7d": aa0,
        "active_days_30d": len(days),
        "hints_avg_7d": avg_hints(last7),
    }


def sessions_per_day_from_logs(series: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Approximate 'interaction days' from task log timestamps."""
    day_counts: dict[str, int] = defaultdict(int)
    for r in series:
        ts = _parse_ts(str(r.get("session_timestamp", "")))
        if ts:
            day_counts[ts.strftime("%Y-%m-%d")] += 1
    return [{"day": d, "events": day_counts[d]} for d in sorted(day_counts.keys())]
