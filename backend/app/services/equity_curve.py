from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Literal, Tuple

import akshare as ak
import pandas as pd


def _normalize_date(date_str: str) -> str:
    """
    Normalize dates to `YYYY-MM-DD` for reliable string comparison.
    AkShare might return `YYYYMMDD` or `YYYY-MM-DD`.
    """

    s = (date_str or "").strip()
    if not s:
        raise ValueError("empty date_str")
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    if len(s) == 8 and s.isdigit():
        return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"
    # best-effort fallback
    return s[:10]


def _ts_to_op_date(timestamp: str) -> str:
    # operation.json uses "YYYY-MM-DD HH:mm:ss"
    return (timestamp or "")[:10]


def _first_trading_date_ge(trading_dates: List[str], op_date: str) -> str | None:
    for d in trading_dates:
        if d >= op_date:
            return d
    return None


InstrumentType = Literal["etf", "stock", "index"]


def _strip_exchange_prefix(symbol: str) -> str:
    s = (symbol or "").strip().lower()
    if s.startswith(("sh", "sz", "bj")) and len(s) >= 8:
        return s[-6:]
    return s


def _ensure_index_symbol(symbol: str) -> str:
    """
    Normalize to AkShare index symbol format, e.g. `sh000001`, `sz399001`.
    """
    s = (symbol or "").strip().lower()
    if s.startswith(("sh", "sz")) and len(s) == 8:
        return s
    raw = _strip_exchange_prefix(s)
    if len(raw) != 6 or not raw.isdigit():
        return s
    # best-effort defaults
    if raw.startswith("399"):
        return f"sz{raw}"
    return f"sh{raw}"


def _ensure_etf_symbol(symbol: str) -> Tuple[str, str]:
    """
    Returns (prefixed_symbol, plain_6_digit_symbol) for ETF.
    Example: `510300` -> (`sh510300`, `510300`)
    """
    s = (symbol or "").strip().lower()
    if s.startswith(("sh", "sz")) and len(s) == 8:
        return s, s[-6:]
    raw = _strip_exchange_prefix(s)
    if len(raw) != 6 or not raw.isdigit():
        return s, raw
    # heuristic: 5xxxx ETFs are usually Shanghai
    prefix = "sh" if raw.startswith(("5", "6", "9")) else "sz"
    return f"{prefix}{raw}", raw


def _fetch_price_history(
    instrument_type: InstrumentType,
    symbol: str,
    start_date: str,
    end_date: str,
    adjust: str,
) -> pd.DataFrame:
    """
    Return DataFrame with columns: date (YYYY-MM-DD), close (float).
    `start_date`/`end_date` are `YYYYMMDD`.
    """
    if instrument_type == "index":
        idx = _ensure_index_symbol(symbol)
        df = ak.stock_zh_index_daily(symbol=idx)
        # try common column conventions
        if "date" not in df.columns:
            df = df.rename(columns={"日期": "date"})
        if "close" not in df.columns:
            df = df.rename(columns={"收盘": "close"})
        df = df[["date", "close"]].copy()
        df["date"] = df["date"].astype(str).apply(_normalize_date)
        df["close"] = df["close"].astype(float)
        df = df.sort_values("date")
        # slice by requested range
        start_norm = _normalize_date(f"{start_date[0:4]}-{start_date[4:6]}-{start_date[6:8]}")
        end_norm = _normalize_date(f"{end_date[0:4]}-{end_date[4:6]}-{end_date[6:8]}")
        return df[(df["date"] >= start_norm) & (df["date"] <= end_norm)]

    if instrument_type == "stock":
        raw = _strip_exchange_prefix(symbol)
        df = ak.stock_zh_a_hist(
            symbol=raw,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
        )
        if "date" not in df.columns:
            df = df.rename(columns={"日期": "date"})
        if "close" not in df.columns:
            df = df.rename(columns={"收盘": "close"})
        df = df[["date", "close"]].copy()
        df["date"] = df["date"].astype(str).apply(_normalize_date)
        df["close"] = df["close"].astype(float)
        return df.sort_values("date")

    # etf
    prefixed, raw = _ensure_etf_symbol(symbol)
    # Prefer Sina for prefixed symbol (matches your local test artifacts).
    try:
        df = ak.fund_etf_hist_sina(symbol=prefixed)
        if "date" not in df.columns:
            df = df.rename(columns={"date": "date", "日期": "date"})
        if "close" not in df.columns:
            df = df.rename(columns={"close": "close", "收盘": "close"})
        df = df[["date", "close"]].copy()
        df["date"] = df["date"].astype(str).apply(_normalize_date)
        df["close"] = df["close"].astype(float)
        df = df.sort_values("date")
        start_norm = _normalize_date(f"{start_date[0:4]}-{start_date[4:6]}-{start_date[6:8]}")
        end_norm = _normalize_date(f"{end_date[0:4]}-{end_date[4:6]}-{end_date[6:8]}")
        df = df[(df["date"] >= start_norm) & (df["date"] <= end_norm)]
        if not df.empty:
            return df
    except Exception:
        # fall back to EM below
        pass

    df = ak.fund_etf_hist_em(
        symbol=raw,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust=adjust,
    )
    if "date" not in df.columns:
        df = df.rename(columns={"日期": "date"})
    if "close" not in df.columns:
        df = df.rename(columns={"收盘": "close"})
    df = df[["date", "close"]].copy()
    df["date"] = df["date"].astype(str).apply(_normalize_date)
    df["close"] = df["close"].astype(float)
    return df.sort_values("date")


def compute_equity_curve(
    stock_code: str,
    initial_capital: float,
    operations: List,
    instrument_type: InstrumentType = "etf",
    adjust: str = "qfq",
    days_back: int = 120,
) -> Dict:
    """
    Build an equity curve based on ETF daily close price (not cost avg).

    points:
      - daily trading dates from akshare
      - total_assets = cash + position_qty * close

    trade_markers:
      - each operation is aligned to the first available trading date >= op_date
    """

    ops = [op for op in operations if getattr(op, "stock_code", None) == stock_code]
    ops_sorted = sorted(ops, key=lambda o: getattr(o, "timestamp"))

    if not ops_sorted:
        return {
            "stock_code": stock_code,
            "start_date": "",
            "end_date": "",
            "points": [],
            "trade_markers": [],
        }

    op_dates = [_ts_to_op_date(op.timestamp) for op in ops_sorted]
    earliest = min(op_dates)
    latest = max(op_dates)

    earliest_dt = datetime.strptime(earliest, "%Y-%m-%d")
    latest_dt = datetime.strptime(latest, "%Y-%m-%d")

    # extra buffer for holidays / missing close on the exact op_date
    start_date = (earliest_dt - timedelta(days=days_back)).strftime("%Y%m%d")
    end_date = (latest_dt + timedelta(days=7)).strftime("%Y%m%d")

    df = _fetch_price_history(
        instrument_type=instrument_type,
        symbol=stock_code,
        start_date=start_date,
        end_date=end_date,
        adjust=adjust,
    )
    if "date" not in df.columns or "close" not in df.columns:
        raise ValueError(f"akshare response missing required columns for {instrument_type}:{stock_code}")

    df = df[["date", "close"]].copy()
    df["date"] = df["date"].astype(str).apply(_normalize_date)
    df["close"] = df["close"].astype(float)
    df = df.sort_values("date")

    # slice to keep points compact (but still allow marker alignment forward)
    trading_dates_all = df["date"].tolist()
    trading_dates = [d for d in trading_dates_all if d >= earliest]
    trading_dates = trading_dates[: max(1, len(trading_dates))]  # ensure non-empty slice
    if not trading_dates:
        raise ValueError(f"no trading dates available for {stock_code}")

    close_map: Dict[str, float] = {d: float(c) for d, c in zip(df["date"], df["close"])}

    cash = float(initial_capital)
    position_qty = 0.0
    op_index = 0

    points: List[Dict] = []
    for d in trading_dates:
        while op_index < len(ops_sorted) and _ts_to_op_date(ops_sorted[op_index].timestamp) <= d:
            op = ops_sorted[op_index]
            if op.type == "buy":
                cash -= float(op.total_amount)
                position_qty += float(op.quantity)
            else:
                cash += float(op.total_amount)
                position_qty -= float(op.quantity)
            op_index += 1

        close_price = close_map.get(d)
        if close_price is None:
            # should not happen because close_map built from df dates
            continue

        market_value = position_qty * close_price
        total_assets = cash + market_value
        nav = total_assets / float(initial_capital)

        points.append(
            {
                "date": d,
                "total_assets": round(total_assets, 6),
                "cash": round(cash, 6),
                "market_value": round(market_value, 6),
                "position_quantity": round(position_qty, 6),
                "close_price": round(close_price, 6),
                "nav": round(nav, 8),
            }
        )

    if not points:
        raise ValueError(f"failed to build equity points for {stock_code}")

    points_by_date = {p["date"]: p["total_assets"] for p in points}

    trade_markers: List[Dict] = []
    for op in ops_sorted:
        op_date = _ts_to_op_date(op.timestamp)
        assigned_date = _first_trading_date_ge(trading_dates, op_date)
        if assigned_date is None:
            # operations after the last point
            assigned_date = points[-1]["date"]
        trade_markers.append(
            {
                "date": assigned_date,
                "type": op.type,
                "timestamp": op.timestamp,
                "stock_code": op.stock_code,
                "stock_name": op.stock_name,
                "price": float(op.price),
                "quantity": float(op.quantity),
                "total_amount": float(op.total_amount),
                "total_assets_at_marker": points_by_date.get(assigned_date, points_by_date[points[-1]["date"]]),
            }
        )

    return {
        "stock_code": stock_code,
        "start_date": points[0]["date"],
        "end_date": points[-1]["date"],
        "points": points,
        "trade_markers": trade_markers,
    }

