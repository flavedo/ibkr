import { ref } from 'vue'
import { fetchExchangeRate } from '@/api/account'

type CurrencyCode = 'USD' | 'CNH'

const currentCurrency = ref<CurrencyCode>('USD')
const exchangeRate = ref(1)
const loading = ref(false)

export function useCurrency() {
  async function switchCurrency(currency: CurrencyCode) {
    if (currency === currentCurrency.value) return
    currentCurrency.value = currency
    if (currency === 'CNH') {
      loading.value = true
      try {
        const response = await fetchExchangeRate('USD', 'CNH')
        exchangeRate.value = response.rate
      } catch {
        exchangeRate.value = 7.25
      } finally {
        loading.value = false
      }
    } else {
      exchangeRate.value = 1
    }
  }

  function convertValue(value: number | null): number | null {
    if (value === null || value === undefined) return null
    return value * exchangeRate.value
  }

  function currencySymbol(): string {
    return currentCurrency.value === 'CNH' ? '¥' : '$'
  }

  function formatConverted(value: number | null, digits = 2): string {
    const converted = convertValue(value)
    if (converted === null) return '--'
    return new Intl.NumberFormat('zh-CN', {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    }).format(converted)
  }

  function formatConvertedSigned(value: number | null, digits = 2): string {
    const converted = convertValue(value)
    if (converted === null) return ''
    const prefix = converted > 0 ? '+' : ''
    return `${prefix}${formatNumber(Math.abs(converted), digits)}`
  }

  function formatNumber(value: number, digits = 2): string {
    return new Intl.NumberFormat('zh-CN', {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    }).format(value)
  }

  return {
    currentCurrency,
    exchangeRate,
    loading,
    switchCurrency,
    convertValue,
    currencySymbol,
    formatConverted,
    formatConvertedSigned,
  }
}
