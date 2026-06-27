import api from './auth'

export const priceApi = {
  getPrices(params) {
    return api.get('/prices', { params })
  },
  getLatestPrices(params) {
    return api.get('/prices/latest', { params })
  },
  getPriceHistory(productId, days = 30, source) {
    return api.get(`/prices/history/${productId}`, { params: source ? { days, source } : { days } })
  },
  getStatsSummary(source) {
    return api.get('/prices/stats/summary', { params: source ? { source } : {} })
  },
  // Dashboard API
  getDashboardDistribution(params) {
    return api.get('/prices/dashboard/distribution', { params })
  },
  getDashboardRanking(params) {
    return api.get('/prices/dashboard/ranking', { params })
  },
  getDashboardIndicatorCards(params) {
    return api.get('/prices/dashboard/indicator-cards', { params })
  },
  getDashboardVolatility(params) {
    return api.get('/prices/dashboard/volatility', { params })
  },
  getDashboardHistoryCompare(productIds, days = 30, categoryId, subcategoryId, source, industry) {
    const params = { days }
    if (productIds) params.product_ids = productIds
    if (categoryId) params.category_id = categoryId
    if (subcategoryId) params.subcategory_id = subcategoryId
    if (source) params.source = source
    if (industry) params.industry = industry
    return api.get('/prices/dashboard/history/compare', { params })
  },
  getBenchmarkHistory(productId, days = 30, source) {
    return api.get(`/prices/benchmark/history/${productId}`, {
      params: source ? { days, source } : { days }
    })
  },
  getBenchmarkHistoryMulti(params) {
    // params: { productIds, days, categoryId, subcategoryId, source, industry }
    return api.get('/prices/benchmark/history', { params })
  },
  getSupplierComparison(params) {
    // params: { product_id, days, source, industry }
    return api.get('/prices/supplier-comparison', { params })
  }
}

export const priceRecordApi = {
  createPriceRecord(data) {
    return api.post('/prices', data)
  },
  updatePriceRecord(id, data) {
    return api.put(`/prices/${id}`, data)
  },
  deletePriceRecord(id) {
    return api.delete(`/prices/${id}`)
  }
}