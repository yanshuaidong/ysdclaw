"""
用于测试：当前运行环境是否能从 akshare 成功拉取 510300（沪深300ETF）日线数据。

你之前遇到 RemoteDisconnected / Connection aborted，这个脚本会把异常打印出来，便于定位：
1) 网络是否可达
2) 请求是否被对端断开
3) akshare 接口是否可用
"""

from __future__ import annotations

from datetime import datetime, timedelta
import os
import time


def main() -> None:
    stock_code = "510300"
    days = int(os.getenv("AKSHARE_TEST_DAYS", "10"))
    retries = int(os.getenv("AKSHARE_TEST_RETRIES", "3"))
    base_sleep_seconds = float(os.getenv("AKSHARE_TEST_SLEEP_SECONDS", "2"))
    # 如果你明确希望“没有网络也算失败”，把该环境变量设为 1
    required = os.getenv("AKSHARE_TEST_REQUIRED", "0") == "1"

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    print(f"Testing akshare for {stock_code} from {start_date} to {end_date} ...")

    def is_connection_related_error(err: Exception) -> bool:
        # akshare/requests/urllib3 在不同环境里抛出的异常类型可能不同，
        # 这里通过关键字兜底判断是否属于连接类问题。
        msg = str(err).lower()
        type_name = type(err).__name__.lower()
        connection_keywords = (
            "connection aborted",
            "remote end closed connection",
            "remotedisconnected",
            "connectionerror",
            "max retries",
            "timeout",
            "timed out",
            "dns",
            "name or service not known",
            "refused",
            "reset by peer",
            "protocolerror",
        )
        return any(k in msg or k in type_name for k in connection_keywords)

    import akshare as ak

    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            df = ak.fund_etf_hist_em(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",
            )

            if df is None or len(df) == 0:
                raise ValueError("akshare returned empty dataframe")

            # 尽量只打印必要信息，避免输出过大
            print("Success.")
            print("Columns:", list(df.columns))
            print("Rows:", len(df))
            print("Head:")
            print(df.head(3).to_string(index=False))
            return
        except Exception as e:
            last_err = e
            is_conn_err = is_connection_related_error(e)

            if attempt < retries and is_conn_err:
                sleep_s = base_sleep_seconds * (2 ** (attempt - 1))
                print(
                    f"Fetch failed (connection issue). Attempt {attempt}/{retries}, retrying in {sleep_s:.1f}s..."
                )
                time.sleep(sleep_s)
                continue
            # 最终一次（或非连接类异常）
            if is_conn_err:
                print(
                    f"Connection issue persists after {attempt}/{retries} attempts; treating as skip."
                )
                print("Error type:", type(e).__name__)
                print("Error message:", str(e))
                if required:
                    # CI/你明确要求时才让连接异常导致失败
                    raise
                return

            # 非连接类异常：直接失败（更容易定位真实问题）
            print("Failed to fetch from akshare.")
            print("Error type:", type(e).__name__)
            print("Error message:", str(e))
            raise

    # 理论上走到这里表示重试也失败了（但兜底处理）
    if last_err is not None:
        if required:
            raise last_err
        print("Treating as skip (set AKSHARE_TEST_REQUIRED=1 to enforce failure).")


if __name__ == "__main__":
    main()

