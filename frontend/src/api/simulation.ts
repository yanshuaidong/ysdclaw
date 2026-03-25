import api from './index'

export type SimulationOperation = {
  type: 'buy' | 'sell'
  stock_code: string
  stock_name: string
  price: number
  quantity: number
  total_amount: number
  timestamp: string
}

export type EquityPoint = {
  date: string
  total_assets: number
  cash: number
  market_value: number
  position_quantity: number
  close_price: number
  nav: number
}

export type TradeMarker = {
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

export type EquityCurveResponse = {
  stock_code: string
  start_date: string
  end_date: string
  points: EquityPoint[]
  trade_markers: TradeMarker[]
}

export async function fetchEquityCurve(req: {
  stock_code: string
  instrument_type?: 'etf' | 'stock' | 'index'
  initial_capital: number
  operations: SimulationOperation[]
  adjust?: string
  days_back?: number
}): Promise<EquityCurveResponse> {
  const { data } = await api.post<EquityCurveResponse>('/simulations/equity-curve', req)
  return data
}

