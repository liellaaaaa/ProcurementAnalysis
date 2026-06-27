import api from './index'

export const reportApi = {
  getWeeklyStats() {
    return api.get('/prices/stats/weekly')
  },
  getMonthlyStats(month) {
    return api.get('/prices/stats/monthly', { params: month ? { month } : {} })
  },
  getRanking(days = 7) {
    return api.get('/prices/dashboard/ranking', { params: { days } })
  },
  getForecast(productId, days = 30) {
    return api.get(`/prices/forecast/${productId}`, { params: { days } })
  },
  compareProducts(ids) {
    return api.get('/prices/compare', { params: { product_ids: ids } })
  },
  downloadPdf(type = 'weekly', startDate = null, endDate = null, industry = null, source = null) {
    const params = { report_type: type }
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    if (industry) params.industry = industry
    if (source) params.source = source
    return api.get('/reports/pdf', { params, responseType: 'blob' })
  },
  downloadExcel(type = 'weekly', startDate = null, endDate = null, industry = null, source = null) {
    const params = { report_type: type }
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    if (industry) params.industry = industry
    if (source) params.source = source
    return api.get('/reports/excel', { params, responseType: 'blob' })
  },
  downloadHtml(type = 'weekly', startDate = null, endDate = null, industry = null, source = null) {
    const params = { report_type: type }
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    if (industry) params.industry = industry
    if (source) params.source = source
    return api.get('/reports/html', { params, responseType: 'blob' })
  }
}