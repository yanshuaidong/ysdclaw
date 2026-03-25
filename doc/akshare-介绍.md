# AkShare 接口介绍：历史行情数据

本页汇总项目中常用的 AkShare **历史行情数据**相关接口，重点覆盖：东财（推荐优先使用）、新浪、腾讯，以及通用的复权说明。

> 经验建议：如无特殊原因，建议优先使用 `stock_zh_a_hist`（数据质量高，访问限制相对少）。

---

## 历史行情数据-东财

接口：`stock_zh_a_hist`

目标地址（示例）：https://quote.eastmoney.com/concept/sh603777.html?from=classic

描述：东方财富-沪深京 A 股日频历史数据。历史数据按日频率更新；**当日收盘价请在收盘后获取**。

限量：单次返回指定沪深京 A 股上市公司、指定周期与指定日期间的历史行情日频率数据。

输入参数

| 名称 | 类型 | 说明 |
|---|---|---|
| `symbol` | `str` | 股票代码（示例：`"603777"`）。股票代码可在 `ak.stock_zh_a_spot_em()` 获取 |
| `period` | `str` | 周期（示例：`"daily"`）。可选：`{"daily","weekly","monthly"}` |
| `start_date` | `str` | 开始日期（示例：`"20210301"`） |
| `end_date` | `str` | 结束日期（示例：`"20210616"`） |
| `adjust` | `str` | 默认不复权；`qfq` 前复权；`hfq` 后复权 |
| `timeout` | `float` | 超时时间（默认 `None`，表示不设置超时） |

股票数据复权（`adjust`）

- 不复权：返回原始价格序列（不保证跨时间点的连续性）。
- 前复权（`qfq`）：保持“当前价格不变”，对历史价格做增减，使历史价格连续。缺点是历史前复权价格会随除权除息事件“时变”。
- 后复权（`hfq`）：保持“历史价格不变”，在权益事件发生后调整“当前价格”，后复权序列更适合做长期收益/量化研究。

输出参数-历史行情数据

| 名称 | 类型 | 描述 |
|---|---|---|
| 日期 | `object` | 交易日 |
| 股票代码 | `object` | 不带市场标识的股票代码 |
| 开盘 | `float64` | 开盘价 |
| 收盘 | `float64` | 收盘价 |
| 最高 | `float64` | 最高价 |
| 最低 | `float64` | 最低价 |
| 成交量 | `int64` | 注意单位：手 |
| 成交额 | `float64` | 注意单位：元 |
| 振幅 | `float64` | 注意单位：% |
| 涨跌幅 | `float64` | 注意单位：% |
| 涨跌额 | `float64` | 注意单位：元 |
| 换手率 | `float64` |  |

接口示例-历史行情数据（不复权）

```python
import akshare as ak

stock_zh_a_hist_df = ak.stock_zh_a_hist(
    symbol="000001",
    period="daily",
    start_date="20170301",
    end_date="20240528",
    adjust="",
)
print(stock_zh_a_hist_df)
```

接口示例-历史行情数据（前复权）

```python
import akshare as ak

stock_zh_a_hist_df = ak.stock_zh_a_hist(
    symbol="000001",
    period="daily",
    start_date="20170301",
    end_date="20240528",
    adjust="qfq",
)
print(stock_zh_a_hist_df)
```

接口示例-历史行情数据（后复权）

```python
import akshare as ak

stock_zh_a_hist_df = ak.stock_zh_a_hist(
    symbol="000001",
    period="daily",
    start_date="20170301",
    end_date="20240528",
    adjust="hfq",
)
print(stock_zh_a_hist_df)
```

---

## 历史行情数据-新浪

接口：`stock_zh_a_daily`

目标地址（示例）：https://finance.sina.com.cn/realstock/company/sh600006/nc.shtml

描述：新浪财经-沪深京 A 股日频历史数据；历史数据按日频率更新。注意：其中 `sh689009` 为 CDR，请通过 `ak.stock_zh_a_cdr_daily` 获取。

限量：单次返回指定沪深京 A 股上市公司、指定日期间的历史行情日频率数据；多次获取容易封禁 IP。

输入参数

| 名称 | 类型 | 说明 |
|---|---|---|
| `symbol` | `str` | 带市场标识的股票代码（示例：`"sh600000"`）。股票代码可在 `ak.stock_zh_a_spot()` 获取 |
| `start_date` | `str` | 开始查询日期（示例：`"20201103"`） |
| `end_date` | `str` | 结束查询日期（示例：`"20201116"`） |
| `adjust` | `str` | 不复权：`""`；前复权：`qfq`；后复权：`hfq`；因子：`hfq-factor` / `qfq-factor` |

输出参数-历史行情数据

| 名称 | 类型 | 描述 |
|---|---|---|
| date | `object` | 交易日 |
| open | `float64` | 开盘价 |
| high | `float64` | 最高价 |
| low | `float64` | 最低价 |
| close | `float64` | 收盘价 |
| volume | `float64` | 成交量（单位：股） |
| amount | `float64` | 成交额（单位：元） |
| outstanding_share | `float64` | 流动股本（单位：股） |
| turnover | `float64` | 换手率（`成交量/流动股本`） |

接口示例（前复权）

```python
import akshare as ak

stock_zh_a_daily_qfq_df = ak.stock_zh_a_daily(
    symbol="sh600006",
    start_date="19910403",
    end_date="19910616",
    adjust="qfq",
)
print(stock_zh_a_daily_qfq_df)
```

---

## 历史行情数据-腾讯

接口：`stock_zh_a_hist_tx`

目标地址（示例）：https://gu.qq.com/sh000919/zs

描述：腾讯证券-日频-股票历史数据；历史数据按日频率更新。当日收盘价请在收盘后获取。

限量：单次返回指定沪深京 A 股上市公司、指定周期与指定日期间的历史行情日频率数据；多次获取建议控制频率以避免被限制。

输入参数

| 名称 | 类型 | 说明 |
|---|---|---|
| `symbol` | `str` | 带市场标识（示例：`"sz000001"`） |
| `start_date` | `str` | 开始日期（示例：`"19000101"`） |
| `end_date` | `str` | 结束日期（示例：`"20500101"`） |
| `adjust` | `str` | 不复权：`""`；前复权：`qfq`；后复权：`hfq` |
| `timeout` | `float` | 超时时间（默认 `None`，表示不设置超时） |

输出参数-历史行情数据

| 名称 | 类型 | 描述 |
|---|---|---|
| date | `object` | 交易日 |
| open | `float64` | 开盘价 |
| close | `float64` | 收盘价 |
| high | `float64` | 最高价 |
| low | `float64` | 最低价 |
| amount | `int64` | 注意单位：手（以接口返回为准） |

接口示例（不复权/复权）

```python
import akshare as ak

df = ak.stock_zh_a_hist_tx(
    symbol="sz000001",
    start_date="20200101",
    end_date="20231027",
    adjust="",
)
print(df)
```

---

## 股票数据复权（通用说明）

为何要复权

由于股票存在配股、分拆、合并和发放股息等事件，会导致股价出现“价格缺口”。如果使用不复权价格去做指标计算或收益率计算，通常会破坏序列连续性，从而影响结果。复权的目的就是让序列在研究口径上可比较、可连续。

前复权（`qfq`）

- 保持当前价格不变，对历史价格进行增减，使历史价格连续。
- 便于看盘、叠加技术指标通常更直观顺畅。
- 缺点：除权除息发生后会重新调整历史价格，因此在不同时间点看到的前复权历史数据可能出现差异；对持续分红的公司，前复权价格可能出现负值。

后复权（`hfq`）

- 保持历史价格不变，在权益事件发生后调整当前价格。
- 后复权价更适合用作长期财富增长曲线，反映真实收益率情况。
- 量化投资研究中更常采用后复权数据。

