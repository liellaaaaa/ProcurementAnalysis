import api from './index'

export const priceApi = {
  getPrices(params) {
    return api.get('/prices', { params })
  },
  getLatestPrices(source, page = 1, pageSize = 20, productName = null) {
    return api.get('/prices/latest', { params: { source, page, page_size: pageSize, product_name: productName } })
  },
  getPriceHistory(productId, days = 30, source) {
    return api.get(`/prices/history/${productId}`, { params: source ? { days, source } : { days } })
  },
  getStatsSummary(source) {
    return api.get('/prices/stats/summary', { params: source ? { source } : {} })
  },
  // Dashboard API
  getDashboardDistribution(days = 30) {
    return api.get('/prices/dashboard/distribution', { params: { days } })
  },
  getDashboardRanking(limit = 10, days = 7) {
    return api.get('/prices/dashboard/ranking', { params: { limit, days } })
  },
  getDashboardHistoryCompare(productIds, days = 30) {
    return api.get('/prices/dashboard/history/compare', { params: { product_ids: productIds, days } })
  },
  getDashboardVolatility(days = 7) {
    return api.get('/prices/dashboard/volatility', { params: { days } })
  }
}

export const productApi = {
  getProducts(params) {
    return api.get('/products', { params })
  },
  getProduct(id) {
    return api.get(`/products/${id}`)
  },
  createProduct(data) {
    return api.post('/products', data)
  },
  updateProduct(id, data) {
    return api.put(`/products/${id}`, data)
  },
  deleteProduct(id) {
    return api.delete(`/products/${id}`)
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

export const reportApi = {
  getWeeklyStats() {
    return api.get('/prices/stats/weekly')
  },
  getMonthlyStats(month) {
    return api.get('/prices/stats/monthly', { params: month ? { month } : {} })
  },
  getRanking(days = 7) {
    return api.get('/prices/stats/ranking', { params: { days } })
  },
  getForecast(productId, days = 30) {
    return api.get(`/prices/forecast/${productId}`, { params: { days } })
  },
  compareProducts(ids) {
    return api.get('/prices/compare', { params: { product_ids: ids } })
  },
  downloadPdf(type = 'weekly') {
    return api.get('/reports/pdf', { params: { report_type: type }, responseType: 'blob' })
  },
  downloadExcel(type = 'weekly') {
    return api.get('/reports/excel', { params: { report_type: type }, responseType: 'blob' })
  }
}

export const alertApi = {
  getAlertConfigs(params) {
    return api.get('/alerts/configs', { params })
  },
  createAlertConfig(data) {
    return api.post('/alerts/configs', data)
  },
  updateAlertConfig(id, data) {
    return api.put(`/alerts/configs/${id}`, data)
  },
  deleteAlertConfig(id) {
    return api.delete(`/alerts/configs/${id}`)
  },
  getAlertRecords(params) {
    return api.get('/alerts', { params })
  },
  markAsRead(id) {
    return api.put(`/alerts/${id}/read`)
  },
  markAllAsRead() {
    return api.put('/alerts/read-all')
  },
  deleteAlertRecord(id) {
    return api.delete(`/alerts/${id}`)
  }
}

export const scraperApi = {
  checkFreshness() {
    return api.get('/check-freshness')
  },
  runScraper(source) {
    return api.post(`/scrapers/${source}/run`)
  }
}