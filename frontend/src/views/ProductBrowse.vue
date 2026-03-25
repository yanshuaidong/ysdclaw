<template>
  <div class="product-browse" v-loading="loading" element-loading-text="加载数据中...">
    <el-result v-if="error" icon="error" title="数据加载失败" :sub-title="error">
      <template #extra>
        <el-button type="primary" @click="loadData">重试</el-button>
      </template>
    </el-result>

    <el-empty v-else-if="!loading && !accountData" description="暂无复盘数据" />

    <template v-else-if="!loading">
      <div class="page-header">
        <h2>华泰柏瑞沪深300ETF · 模拟交易</h2>
        <el-tag type="success" effect="dark" size="large">510300</el-tag>
      </div>

      <!-- 第一层：情况概览 -->
      <el-row :gutter="16" class="overview-row">
        <el-col :span="8">
          <div class="overview-card primary">
            <div class="card-label">总资产</div>
            <div class="card-value">¥ {{ formatMoney(account.total_assets) }}</div>
            <div class="card-sub">
              <span :class="profitRateClass">{{ profitRateText }}</span>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="overview-card">
            <div class="card-label">可用资金</div>
            <div class="card-value">¥ {{ formatMoney(account.available_funds) }}</div>
            <div class="card-sub">占比 {{ fundRatio }}%</div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="overview-card">
            <div class="card-label">持仓市值</div>
            <div class="card-value">¥ {{ formatMoney(account.total_market_value) }}</div>
            <div class="card-sub">占比 {{ marketRatio }}%</div>
          </div>
        </el-col>
      </el-row>
      <el-row :gutter="16" class="overview-row">
        <el-col :span="8">
          <div class="overview-card">
            <div class="card-label">持仓数量</div>
            <div class="card-value">{{ position.quantity }} 份</div>
            <div class="card-sub">{{ position.name }}</div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="overview-card">
            <div class="card-label">持仓均价</div>
            <div class="card-value">¥ {{ position.avg_cost.toFixed(3) }}</div>
            <div class="card-sub">成本总额 ¥ {{ formatMoney(position.quantity * position.avg_cost) }}</div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="overview-card">
            <div class="card-label">交易次数</div>
            <div class="card-value">{{ operations.length }} 笔</div>
            <div class="card-sub">买入 {{ buyCount }} 笔 / 卖出 {{ sellCount }} 笔</div>
          </div>
        </el-col>
      </el-row>

      <!-- 第二层：总资产折线图 -->
      <el-card shadow="never" class="chart-card">
        <template #header>
          <div class="card-header">
            <span>总资产走势</span>
            <el-tag size="small" type="info">初始资金 ¥10,000.00</el-tag>
            <el-tag v-if="chartError" size="small" type="danger">净值曲线加载失败</el-tag>
          </div>
        </template>
        <div ref="chartRef" class="chart-container"></div>
      </el-card>

      <!-- 第三层：交易列表 -->
      <el-card shadow="never" class="table-card">
        <template #header>
          <div class="card-header">
            <span>交易记录</span>
            <el-tag size="small">共 {{ operations.length }} 条</el-tag>
          </div>
        </template>
        <el-table :data="operations" stripe border style="width: 100%">
          <el-table-column label="时间" prop="timestamp" width="200" />
          <el-table-column label="方向" prop="type" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.type === 'buy' ? 'danger' : 'success'" effect="dark" size="small">
                {{ row.type === 'buy' ? '买入' : '卖出' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="代码" prop="stock_code" width="100" align="center" />
          <el-table-column label="名称" prop="stock_name" />
          <el-table-column label="价格" prop="price" width="120" align="right">
            <template #default="{ row }">
              ¥ {{ row.price.toFixed(3) }}
            </template>
          </el-table-column>
          <el-table-column label="数量" prop="quantity" width="100" align="right">
            <template #default="{ row }">
              {{ row.quantity }} 份
            </template>
          </el-table-column>
          <el-table-column label="成交金额" prop="total_amount" width="140" align="right">
            <template #default="{ row }">
              <span :class="row.type === 'buy' ? 'text-red' : 'text-green'">
                ¥ {{ formatMoney(row.total_amount) }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  MarkPointComponent,
  MarkLineComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { fetchJson } from '../api/openclaw'
import { fetchEquityCurve } from '../api/simulation'

echarts.use([
  LineChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  MarkPointComponent,
  MarkLineComponent,
  CanvasRenderer,
])

const INITIAL_CAPITAL = 10000
const TARGET_STOCK_CODE = '510300'

interface AccountData {
  available_funds: number
  total_market_value: number
  total_assets: number
  positions: Record<string, { name: string; quantity: number; avg_cost: number }>
}

interface Operation {
  type: 'buy' | 'sell'
  stock_code: string
  stock_name: string
  price: number
  quantity: number
  total_amount: number
  timestamp: string
}

interface EquityPoint {
  date: string
  total_assets: number
  cash: number
  market_value: number
  position_quantity: number
  close_price: number
  nav: number
}

interface TradeMarker {
  date: string
  type: 'buy' | 'sell'
  timestamp: string
  stock_code: string
  stock_name: string
  price: number
  quantity: number
  total_amount: number
  total_assets_at_marker: number
}

const loading = ref(true)
const error = ref('')
const chartError = ref('')
const accountData = ref<AccountData | null>(null)
const operationsData = ref<Operation[]>([])
const equityPoints = ref<EquityPoint[]>([])
const tradeMarkers = ref<TradeMarker[]>([])

const lastEquityPoint = computed(() => {
  if (equityPoints.value.length === 0) return null
  return equityPoints.value[equityPoints.value.length - 1]
})

const account = computed(() => {
  const p = lastEquityPoint.value
  if (p) {
    return {
      available_funds: p.cash,
      total_market_value: p.market_value,
      total_assets: p.total_assets,
    }
  }
  const a = accountData.value
  if (!a) return { available_funds: 0, total_market_value: 0, total_assets: INITIAL_CAPITAL }
  return {
    available_funds: a.available_funds,
    total_market_value: a.total_market_value,
    total_assets: a.total_assets,
  }
})

const position = computed(() => {
  const a = accountData.value
  const p = a?.positions?.['510300']
  if (!p || p.quantity === 0) {
    return { name: '华泰柏瑞沪深300ETF', quantity: 0, avg_cost: 0 }
  }
  return { name: p.name, quantity: p.quantity, avg_cost: p.avg_cost }
})

const operations = computed(() => operationsData.value)

const buyCount = computed(() => operations.value.filter(o => o.type === 'buy').length)
const sellCount = computed(() => operations.value.filter(o => o.type === 'sell').length)

const profitRate = computed(() =>
  ((account.value.total_assets - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100
)
const profitRateClass = computed(() =>
  profitRate.value > 0 ? 'text-green' : profitRate.value < 0 ? 'text-red' : 'text-neutral'
)
const profitRateText = computed(() => {
  const sign = profitRate.value > 0 ? '+' : ''
  return `收益率 ${sign}${profitRate.value.toFixed(2)}%`
})

const fundRatio = computed(() => {
  if (account.value.total_assets === 0) return '0.0'
  return ((account.value.available_funds / account.value.total_assets) * 100).toFixed(1)
})
const marketRatio = computed(() => {
  if (account.value.total_assets === 0) return '0.0'
  return ((account.value.total_market_value / account.value.total_assets) * 100).toFixed(1)
})

function formatMoney(val: number) {
  return val.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// --- ECharts ---
const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

function buildChartData() {
  if (equityPoints.value.length === 0) return []
  return equityPoints.value.map(p => ({ time: p.date, value: p.total_assets }))
}

function initChart() {
  if (!chartRef.value) return
  chartInstance?.dispose()
  chartInstance = echarts.init(chartRef.value)

  const data = buildChartData()
  if (data.length === 0) return

  const markersByDate = new Map<string, TradeMarker[]>()
  for (const m of tradeMarkers.value) {
    if (!markersByDate.has(m.date)) markersByDate.set(m.date, [])
    markersByDate.get(m.date)!.push(m)
  }

  const markPointData = tradeMarkers.value.map(m => ({
    coord: [m.date, m.total_assets_at_marker],
    value: m.type === 'buy' ? '买入' : '卖出',
    itemStyle: { color: m.type === 'buy' ? '#f56c6c' : '#67c23a' },
  }))

  chartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const p = params[0]
        const date = p.axisValue as string
        const total = Number(p.value)
        const ms = markersByDate.get(date) || []
        const tradeLines =
          ms.length === 0
            ? ''
            : '<br/>交易：' + ms.map(m => `${m.type === 'buy' ? '买' : '卖'} ¥${m.price.toFixed(3)} × ${m.quantity} (${m.timestamp.slice(11, 16)})`).join('<br/>')

        return `${date}<br/>总资产: <b>¥${total.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}</b>${tradeLines}`
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '12%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.time),
      boundaryGap: false,
      axisLabel: { fontSize: 11, color: '#909399' },
      axisLine: { lineStyle: { color: '#dcdfe6' } },
    },
    yAxis: {
      type: 'value',
      min: (value: any) => Math.floor(value.min * 0.999),
      max: (value: any) => Math.ceil(value.max * 1.001),
      axisLabel: {
        fontSize: 11,
        color: '#909399',
        formatter: (v: number) => `¥${v.toLocaleString()}`,
      },
      splitLine: { lineStyle: { color: '#f0f0f0' } },
    },
    series: [
      {
        type: 'line',
        data: data.map(d => d.value),
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: { width: 3, color: '#409eff' },
        itemStyle: { color: '#409eff', borderWidth: 2, borderColor: '#fff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64,158,255,0.35)' },
            { offset: 1, color: 'rgba(64,158,255,0.02)' },
          ]),
        },
        markLine: {
          silent: true,
          data: [{ yAxis: INITIAL_CAPITAL, label: { formatter: '初始资金' }, lineStyle: { color: '#e6a23c', type: 'dashed' } }],
        },
        markPoint: {
          data: markPointData,
          symbolSize: 12,
          label: { formatter: (p: any) => p.value },
        },
      },
    ],
  })
}

function handleResize() {
  chartInstance?.resize()
}

async function loadData() {
  loading.value = true
  error.value = ''
  chartError.value = ''
  try {
    const [acct, ops] = await Promise.all([
      fetchJson<AccountData>('skills/ysd-account/account.json'),
      fetchJson<Operation[]>('skills/ysd-account/operation.json'),
    ])
    accountData.value = acct
    operationsData.value = ops

    const curveOps = ops.filter(o => o.stock_code === TARGET_STOCK_CODE)
    try {
      const curve = await fetchEquityCurve({
        stock_code: TARGET_STOCK_CODE,
        initial_capital: INITIAL_CAPITAL,
        operations: curveOps,
      })
      equityPoints.value = curve.points
      tradeMarkers.value = curve.trade_markers
    } catch (e: any) {
      chartError.value = e?.message || '净值曲线接口失败'
    }
  } catch (e: any) {
    error.value = e.message || '加载数据失败'
  } finally {
    loading.value = false
    await nextTick()
    // Ensure chart container is mounted (template is gated by `!loading`)
    if (!chartError.value && equityPoints.value.length > 0) {
      initChart()
    }
  }
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<style lang="scss" scoped>
.product-browse {
  padding-bottom: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;

  h2 {
    margin: 0;
    font-size: 22px;
    color: #303133;
    font-weight: 600;
  }
}

.overview-row {
  margin-bottom: 16px;
}

.overview-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px 24px;
  transition: box-shadow 0.2s;

  &:hover {
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  }

  &.primary {
    background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
    border: none;

    .card-label,
    .card-value,
    .card-sub span {
      color: #fff;
    }

    .card-label {
      opacity: 0.85;
    }
  }

  .card-label {
    font-size: 13px;
    color: #909399;
    margin-bottom: 8px;
  }

  .card-value {
    font-size: 24px;
    font-weight: 700;
    color: #303133;
    margin-bottom: 6px;
    font-variant-numeric: tabular-nums;
  }

  .card-sub {
    font-size: 12px;
    color: #909399;
  }
}

.chart-card {
  margin-bottom: 20px;
  border-radius: 8px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 16px;
    font-weight: 600;
    color: #303133;
  }
}

.chart-container {
  width: 100%;
  height: 360px;
}

.table-card {
  border-radius: 8px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 16px;
    font-weight: 600;
    color: #303133;
  }
}

.text-red {
  color: #f56c6c;
}

.text-green {
  color: #67c23a;
}

.text-neutral {
  color: #909399;
}
</style>
