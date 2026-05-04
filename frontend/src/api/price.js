import api from './index'

export const priceApi = {
  getPrices(params) {
    return api.get('/prices', { params })
  },
  getLatestPrices(source) {
    return api.get('/prices/latest', { params: source ? { source } : {} })
  },
  getPriceHistory(productId, days = 30, source) {
    return api.get(`/prices/history/${productId}`, { params: source ? { days, source } : { days } })
  },
  getStatsSummary(source) {
    return api.get('/prices/stats/summary', { params: source ? { source } : {} })
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
  }
}