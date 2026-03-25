# ProductBrowse.vue 说明文档

## 功能概述
`frontend/src/views/ProductBrowse.vue` 用于展示单个标的（默认 `510300`）的“模拟交易复盘”页面，包括：

- 账户总览：总资产、可用资金、持仓市值、持仓数量与均价、交易次数及买卖统计
- 总资产走势：调用后端“净值曲线”接口生成每日曲线点，并绘制折线图（ECharts），同时在曲线上用买卖标记点提示交易发生
- 交易记录：展示 `operation.json` 中的逐笔买入/卖出明细

页面在加载成功后展示内容；加载失败会显示错误信息与“重试”按钮；无数据时展示空状态。

## 页面结构（Template）

页面由以下区域构成：

1. 顶部状态层
   - `v-loading="loading"`：加载态（Element Plus loading）
   - `error`：加载失败展示 `el-result`，并提供重试 `el-button`
   - `!loading && !accountData`：空状态 `el-empty`
2. 顶部页眉
   - 标题：`华泰柏瑞沪深300ETF · 模拟交易`
   - 标记：`<el-tag>510300</el-tag>`
3. 第一层：情况概览（`el-row` + `el-col`）
   - 以卡片形式展示总资产、可用资金、持仓市值
   - 第二行卡片展示持仓数量、持仓均价、交易次数
4. 第二层：总资产折线图（`el-card` + `ref="chartRef"`）
   - ECharts 容器：`chart-container`（固定高度）
5. 第三层：交易列表（`el-card` + `el-table`）
   - 列包括：时间、方向、代码、名称、价格、数量、成交金额
   - 方向使用标签颜色区分：`buy`=红色风格，`sell`=绿色风格

## 数据来源与加载逻辑

页面同时使用“静态 JSON 数据”和“后端曲线接口”：

1) 静态 JSON（通过 `frontend/src/api/openclaw.ts` 的 `fetchJson` 从 `/openclaw-data` 读取）

- `fetchJson<AccountData>('skills/ysd-account/account.json')`
- `fetchJson<Operation[]>('skills/ysd-account/operation.json')`

2) 净值曲线（通过 `frontend/src/api/simulation.ts` 调用后端 `/api`）

- `fetchEquityCurve({ stock_code, initial_capital, operations, instrument_type?, adjust?, days_back? })`
- 实际请求路径：`POST /api/simulations/equity-curve`（详见 `doc/backend-api.md`）

`loadData()` 的关键流程：

- `loading=true`，清空 `error`
- 清空 `chartError`
- 使用 `Promise.all` 并行拉取 `account.json` 与 `operation.json`
- 成功后写入响应式状态：
  - `accountData.value = acct`
  - `operationsData.value = ops`
- 对曲线接口请求的交易记录做过滤：
  - `curveOps = ops.filter(o => o.stock_code === TARGET_STOCK_CODE)`
- 调用后端接口获取曲线点与交易标记：
  - 成功：写入 `equityPoints.value` 与 `tradeMarkers.value`
  - 失败：只设置 `chartError`，页面其余区域仍可正常展示（曲线区域会显示“净值曲线加载失败”标记）
- 失败后：
  - `error.value = e.message || '加载数据失败'`
- finally：
  - `loading=false`
  - 若 `chartError` 为空且 `equityPoints.length > 0`，则初始化 ECharts（`initChart()`）

## 数据模型（TypeScript 接口）

### `AccountData`
```ts
interface AccountData {
  available_funds: number
  total_market_value: number
  total_assets: number
  positions: Record<string, { name: string; quantity: number; avg_cost: number }>
}
```

其中 `positions` 的结构为：

- key：`stock_code`（如 `510300`）
- value：
  - `name`：标的名称
  - `quantity`：持仓数量（单位：份）
  - `avg_cost`：持仓均价（单位：元/份）

### `Operation`
```ts
interface Operation {
  type: 'buy' | 'sell'
  stock_code: string
  stock_name: string
  price: number
  quantity: number
  total_amount: number
  timestamp: string
}
```

页面交易列表直接展示以上字段，并按 `type` 显示买卖方向标签颜色。

## 展示字段映射

页面从 `account.json` 与 `operation.json` 计算/展示内容：

- 总资产/可用资金/持仓市值：
  - 若曲线接口成功（`equityPoints` 有值），优先展示“最后一个曲线点”的实时口径：
    - `total_assets = lastEquityPoint.total_assets`
    - `available_funds = lastEquityPoint.cash`
    - `total_market_value = lastEquityPoint.market_value`
  - 否则回退展示 `account.json` 的字段：
    - `account.total_assets / account.available_funds / account.total_market_value`
- 持仓数量与均价：来自 `account.positions['510300']`（默认只展示 `510300`）
- 交易次数：`operations.length`
- 买入笔数：`operations.filter(o => o.type === 'buy').length`
- 卖出笔数：`operations.filter(o => o.type === 'sell').length`

### 收益率与颜色

收益率使用常量 `INITIAL_CAPITAL = 10000` 计算：

- `profitRate = ((account.total_assets - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100`
- 文案：`收益率 +x.xx% / x.xx%`
- 颜色：
  - `profitRate > 0`：`text-green`
  - `profitRate < 0`：`text-red`
  - 否则：`text-neutral`

## 总资产走势（ECharts）推算逻辑

折线图数据不在前端逐笔推算，而是由后端接口返回后直接渲染。

- 曲线点来自 `equityPoints`（`date` + `total_assets`）
- 交易标记来自 `tradeMarkers`（用于 `markPoint` 与 tooltip 的“交易列表”）

折线图由 `buildChartData()` 把 `equityPoints` 映射成 `{ time, value }` 序列，并在 `initChart()` 中渲染。

### 曲线点口径（后端）

后端的每日点使用“当日收盘价”来计算市值（不是用均价/成本价）：

- `market_value = position_quantity * close_price`
- `total_assets = cash + market_value`
- `nav = total_assets / initial_capital`

图表渲染细节：

- 使用 `echarts/core`（按模块引入）：
  - `LineChart`、`TitleComponent`、`TooltipComponent`、`GridComponent`、`MarkPointComponent`、`MarkLineComponent`
- Tooltip 展示：
  - x 轴日期 + 总资产（`¥` 格式化）
  - 若该日期存在交易标记，则追加“交易明细”（可能同一天多笔）
- markLine：
  - 虚线标记初始资金水平：`yAxis: INITIAL_CAPITAL`
- markPoint：
  - 使用 `tradeMarkers` 绘制买/卖标记点（买入红色、卖出绿色）
- 图形样式：
  - 折线颜色 `#409eff`，面积渐变带浅蓝色阴影

重要说明：曲线是“每日（交易日）曲线”，交易标记会对齐到“第一个交易日 >= 操作日期”，因此操作时间在节假日或非交易日时也能落到最近交易日上。

## 交互与生命周期

- 挂载时：
  - `onMounted()` 调用 `loadData()`
  - 绑定 `window.resize` 事件，触发 `chartInstance.resize()`
- 卸载时：
  - `onBeforeUnmount()` 移除 `resize` 监听
  - 并 `chartInstance.dispose()` 释放资源
- 重试：
  - 错误态显示 `el-button`，点击调用 `loadData()` 重新拉取数据并在成功后重建图表

## 依赖与技术栈

- Vue 3 Composition API：`ref / computed / onMounted / onBeforeUnmount / nextTick`
- Element Plus：`el-result / el-empty / el-card / el-table / el-tag` 等
- ECharts（core 模式）：用于折线图
- 本地数据访问工具：`frontend/src/api/openclaw.ts` 的 `fetchJson`
- 后端曲线接口封装：`frontend/src/api/simulation.ts` 的 `fetchEquityCurve`

## 扩展与注意事项

1. 标的代码硬编码
   - 页面对持仓与页眉使用了固定标的 `510300`：
     - 常量 `TARGET_STOCK_CODE = '510300'`
     - `position` computed 中读取 `accountData.positions['510300']`
     - 页眉标题与 tag 也写死了 `510300`
   - 若要支持多标的，需要同步修改：
     - `TARGET_STOCK_CODE` 的来源（路由参数/选择器）
     - 传给 `fetchEquityCurve` 的 `stock_code`
     - `position` 的取值与页眉展示

2. 数据顺序假设
   - 后端会按 `timestamp` 对 `operations` 排序并生成曲线点；因此 `operation.json` 的顺序不影响曲线计算，但建议保持时间升序便于排查与阅读。

3. operations 为空时不初始化图表
   - 当曲线接口失败（`chartError` 不为空）或 `equityPoints.length === 0` 时不会调用 `initChart()`；页面仍会显示账户总览与表格。

4. JSON 字段匹配
   - `account.json` 与 `operation.json` 字段类型需满足接口定义，否则可能导致渲染异常或 ECharts 推算失败。

