# ProductBrowse.vue 说明文档

## 功能概述
`frontend/src/views/ProductBrowse.vue` 用于展示单个标的（默认 `510300`）的“模拟交易复盘”页面，包括：

- 账户总览：总资产、可用资金、持仓市值、持仓数量与均价、交易次数及买卖统计
- 总资产走势：基于交易记录 `operation.json` 逐笔推算并绘制折线图（ECharts）
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

页面使用 `fetchJson` 从 `frontend/src/api/openclaw.ts` 获取静态 JSON 数据：

- `fetchJson<AccountData>('skills/ysd-account/account.json')`
- `fetchJson<Operation[]>('skills/ysd-account/operation.json')`

`loadData()` 的关键流程：

- `loading=true`，清空 `error`
- 使用 `Promise.all` 并行拉取 `account.json` 与 `operation.json`
- 成功后写入响应式状态：
  - `accountData.value = acct`
  - `operationsData.value = ops`
- 失败后：
  - `error.value = e.message || '加载数据失败'`
- finally：
  - `loading=false`
  - 若未报错且 `operationsData.length > 0`，则初始化 ECharts（`initChart()`）

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

- 总资产：`account.total_assets`
- 可用资金：`account.available_funds`
- 持仓市值：`account.total_market_value`
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

折线图由 `buildChartData()` 生成数据序列，并在 `initChart()` 中渲染。

推算方法要点：

- 初始资金：`funds = INITIAL_CAPITAL (10000)`
- 维护一个内存中的 `positions`（仅用于推算曲线）：
  - `positions[stock_code] = { quantity, avg_cost }`
- 数据点：
  - 起点：`{ time: '初始', value: INITIAL_CAPITAL }`
  - 对每一条 `operation` 依次处理：
    - `buy`：
      - `funds -= op.total_amount`
      - 若已有该 `stock_code` 持仓，则更新均价：
        - `avg_cost = (oldTotal + op.total_amount) / newQuantity`
      - 若无则创建持仓，并令 `avg_cost = op.price`
    - `sell`：
      - `funds += op.total_amount`
      - 减少持仓数量：`quantity -= op.quantity`
      - 若 `quantity <= 0` 则删除该标的持仓（不再参与后续计算）
    - 每笔操作后追加一个点：
      - `time = op.timestamp.slice(0, 10)`（取 `YYYY-MM-DD`）
      - `value = funds + sum(positions[code].quantity * positions[code].avg_cost)`

图表渲染细节：

- 使用 `echarts/core`（按模块引入）：
  - `LineChart`、`TitleComponent`、`TooltipComponent`、`GridComponent`、`MarkPointComponent`、`MarkLineComponent`
- Tooltip 展示：
  - x 轴日期 + 总资产（`¥` 格式化）
- markLine：
  - 虚线标记初始资金水平：`yAxis: INITIAL_CAPITAL`
- 图形样式：
  - 折线颜色 `#409eff`，面积渐变带浅蓝色阴影

重要说明：此处曲线推算基于“成交金额调整现金 + 持仓均价/数量变动”的简化逻辑，具体卖出后均价不再调整（因为卖出只会减少数量或清仓）。

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

## 扩展与注意事项

1. 标的代码硬编码
   - 页面对持仓与页眉使用了固定标的 `510300`：
     - `position` computed 中读取 `accountData.positions['510300']`
     - 页眉标题与 tag 也写死了 `510300`
   - 若要支持多标的，需要：
     - 将 `stock_code` 抽为参数或从路由/配置读取
     - 同步调整标题、持仓展示与走势推算的过滤逻辑（当前图表推算对所有 `operations` 都会累计到 `positions` 中，但展示持仓只看 `510300`）

2. 数据顺序假设
   - `buildChartData()` 逐条按 `operationsData.value` 的顺序推算曲线；因此 `operation.json` 建议保持时间升序或与预期一致。

3. operations 为空时不初始化图表
   - 当 `operationsData.length === 0` 时不会调用 `initChart()`，折线图区域将停留在未渲染状态（页面仍会显示账户总览与表格为空态）。

4. JSON 字段匹配
   - `account.json` 与 `operation.json` 字段类型需满足接口定义，否则可能导致渲染异常或 ECharts 推算失败。

