import api from './auth'

export const scraperApi = {
  checkFreshness() {
    return api.get('/check-freshness')
  },
  runScraper(source) {
    return api.post(`/scrapers/${source}/run`, {}, { timeout: 600000 })
  }
}