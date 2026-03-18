<template>
  <div class="product-browse">
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
        <el-table-column label="时间" prop="timestamp" width="200">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
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
import accountData from '../stores/account.json'
import operationData from '../stores/operation.json'

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

const account = accountData as {
  available_funds: number
  total_market_value: number
  total_assets: number
  positions: Record<string, { name: string; quantity: number; avg_cost: number }>
}

const operations = operationData as Array<{
  type: string
  stock_code: string
  stock_name: string
  price: number
  quantity: number
  total_amount: number
  timestamp: string
}>

const position = account.positions['510300']

const buyCount = computed(() => operations.filter(o => o.type === 'buy').length)
const sellCount = computed(() => operations.filter(o => o.type === 'sell').length)

const profitRate = computed(() =>
  ((account.total_assets - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100
)
const profitRateClass = computed(() =>
  profitRate.value > 0 ? 'text-green' : profitRate.value < 0 ? 'text-red' : 'text-neutral'
)
const profitRateText = computed(() => {
  const sign = profitRate.value > 0 ? '+' : ''
  return `收益率 ${sign}${profitRate.value.toFixed(2)}%`
})

const fundRatio = computed(() =>
  ((account.available_funds / account.total_assets) * 100).toFixed(1)
)
const marketRatio = computed(() =>
  ((account.total_market_value / account.total_assets) * 100).toFixed(1)
)

function formatMoney(val: number) {
  return val.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatTime(ts: string) {
  return ts
}

// --- ECharts ---
const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

function buildChartData() {
  const points: { time: string; value: number }[] = []

  const sortedOps = [...operations].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  )

  if (sortedOps.length > 0) {
    const firstDate = new Date(sortedOps[0].timestamp)
    firstDate.setHours(firstDate.getHours() - 1)
    points.push({
      time: firstDate.toLocaleString('zh-CN'),
      value: INITIAL_CAPITAL,
    })
  }

  let runningAssets = INITIAL_CAPITAL
  for (const op of sortedOps) {
    points.push({
      time: new Date(op.timestamp).toLocaleString('zh-CN'),
      value: runningAssets,
    })
  }

  points.push({
    time: '当前',
    value: account.total_assets,
  })

  return points
}

function initChart() {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)

  const data = buildChartData()

  chartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const p = params[0]
        return `${p.axisValue}<br/>总资产: <b>¥${Number(p.value).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}</b>`
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
      },
    ],
  })
}

function handleResize() {
  chartInstance?.resize()
}

onMounted(async () => {
  await nextTick()
  initChart()
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
