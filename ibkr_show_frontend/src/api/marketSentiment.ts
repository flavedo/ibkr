import { request } from './http'
import { withCache } from '@/utils/cache'

export interface VixRange {
  label: string
  sentiment: string
  strategy: string
  color: string
  is_current: boolean
}

export interface FearGreedRange {
  label: string
  sentiment: string
  strategy: string
  color: string
  is_current: boolean
}

export interface MarketSentimentResponse {
  vix_value: number | null
  vix_level: string
  vix_ranges: VixRange[]
  fear_greed_value: number | null
  fear_greed_level: string
  fear_greed_ranges: FearGreedRange[]
}

export function fetchMarketSentiment(): Promise<MarketSentimentResponse> {
  return withCache(
    'market_sentiment',
    () => request<MarketSentimentResponse>('/api/market-sentiment/')
  )
}
