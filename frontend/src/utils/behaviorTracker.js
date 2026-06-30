/**
 * BehaviorTracker - 前端行为日志追踪器
 * 单例模式，批量发送事件到后端
 */
import { getToken } from '../api/auth'

const API_BASE = '/api/v1'
const BATCH_SIZE = 20
const BATCH_INTERVAL = 5000 // 5 seconds

class BehaviorTracker {
  constructor() {
    this.queue = []
    this.sessionId = null
    this.userId = null
    this.username = null
    this.page = null
    this.lastPageTime = null
    this.timer = null
    this.flushLocked = false

    this._initSession()
    this._initBatchSender()
    this._initVisibilityHandler()
  }

  _initSession() {
    // Try to get existing session from other tabs via BroadcastChannel
    const channel = new BroadcastChannel('bt_session')
    let sessionId = localStorage.getItem('bt_sid')

    if (!sessionId) {
      sessionId = `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`
      localStorage.setItem('bt_sid', sessionId)
    } else {
      // 检查 session 是否过期（>30 分钟无活动则换新）
      const lastActive = localStorage.getItem('bt_last_active')
      if (lastActive && Date.now() - parseInt(lastActive) > 30 * 60 * 1000) {
        sessionId = `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`
        localStorage.setItem('bt_sid', sessionId)
      }
    }
    this.sessionId = sessionId
    localStorage.setItem('bt_last_active', Date.now().toString())

    // Listen for session renew from other tabs
    channel.onmessage = (e) => {
      if (e.data.type === 'SESSION_RENEW') {
        localStorage.setItem('bt_sid', e.data.sessionId)
        this.sessionId = e.data.sessionId
      }
    }

    // Notify other tabs of our session
    channel.postMessage({ type: 'SESSION_JOIN', sessionId: this.sessionId })

    // Parse user from JWT
    const token = getToken()
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]))
        this.userId = payload.user_id || null
        this.username = payload.username || null
      } catch {
        this.userId = null
        this.username = null
      }
    }
  }

  _initBatchSender() {
    this.timer = setInterval(() => {
      if (this.queue.length > 0) {
        this._flush()
      }
    }, BATCH_INTERVAL)
  }

  _initVisibilityHandler() {
    // Flush on page hide (unload)
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        this._flushBeacon()
      }
    })

    // Also flush on beforeunload
    window.addEventListener('beforeunload', () => {
      this._flushBeacon()
    })
  }

  _refreshLastActive() {
    localStorage.setItem('bt_last_active', Date.now().toString())
    // Check if session expired and renew
    const lastActive = localStorage.getItem('bt_last_active')
    if (lastActive && Date.now() - parseInt(lastActive) > 30 * 60 * 1000) {
      this._renewSession()
    }
  }

  _renewSession() {
    const newSessionId = `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`
    localStorage.setItem('bt_sid', newSessionId)
    this.sessionId = newSessionId
    // Notify other tabs
    const channel = new BroadcastChannel('bt_session')
    channel.postMessage({ type: 'SESSION_RENEW', sessionId: newSessionId })
  }

  _flushBeacon() {
    if (this.queue.length === 0) return
    const events = this.queue.splice(0, this.queue.length)
    const data = JSON.stringify({ events })

    // Use sendBeacon for reliable delivery on unload
    if (navigator.sendBeacon) {
      navigator.sendBeacon(`${API_BASE}/operation-logs/behavior`, data)
    } else {
      // Fallback: use sync XHR (blocking, but guaranteed)
      const xhr = new XMLHttpRequest()
      xhr.open('POST', `${API_BASE}/operation-logs/behavior`, false)
      xhr.setRequestHeader('Content-Type', 'application/json')
      if (this.sessionId) {
        xhr.setRequestHeader('X-Session-ID', this.sessionId)
      }
      xhr.send(data)
    }
  }

  async _flush() {
    if (this.flushLocked || this.queue.length === 0) return
    this.flushLocked = true

    const events = this.queue.splice(0, this.queue.length)

    try {
      const res = await fetch(`${API_BASE}/operation-logs/behavior`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-ID': this.sessionId || ''
        },
        body: JSON.stringify({ events }),
        keepalive: true
      })
      if (!res.ok) {
        // Re-queue on failure (max 1 retry)
        this.queue.push(...events)
      }
    } catch {
      // Network error - re-queue
      this.queue.push(...events)
    } finally {
      this.flushLocked = false
    }
  }

  /**
   * Track a behavior event
   * @param {string} module - NAV/UI/BEHAVIOR/PRICE/etc.
   * @param {string} action - PAGE_VIEW/CLICK/FILTER_CHANGE/etc.
   * @param {object} details - Additional event data
   * @param {string} page - Current route
   * @param {string} referrer - Previous route
   */
  track(module, action, details = {}, page = null, referrer = null) {
    this._refreshLastActive()
    const now = new Date()

    // If this is a PAGE_VIEW, record dwell time for previous page
    if (action === 'PAGE_VIEW' && this.lastPageTime && this.page) {
      const dwellMs = now - this.lastPageTime
      // Push STAY event for previous page
      this.queue.push({
        module: 'NAV',
        action: 'STAY',
        details: {
          page: this.page,
          dwell_ms: dwellMs
        },
        page: this.page,
        referrer: referrer || '',
        session_id: this.sessionId,
        timestamp: this.lastPageTime.toISOString(),
        result: 'SUCCESS'
      })
    }

    // Update page tracking state
    if (action === 'PAGE_VIEW') {
      this.lastPageTime = now
      this.page = page || window.location.pathname
    }

    this.queue.push({
      module,
      action,
      details,
      page: page || this.page || window.location.pathname,
      referrer: referrer || (action === 'PAGE_VIEW' ? '' : this._getReferrer()),
      session_id: this.sessionId,
      timestamp: now.toISOString(),
      result: 'SUCCESS'
    })

    // Flush immediately if queue is full
    if (this.queue.length >= BATCH_SIZE) {
      this._flush()
    }
  }

  _getReferrer() {
    try {
      return window.history.state?.from || document.referrer || ''
    } catch {
      return ''
    }
  }

  // Convenience methods
  trackPageView(page) {
    this.track('NAV', 'PAGE_VIEW', {}, page)
  }

  trackClick(elementId, elementType, page, details = {}) {
    this.track('UI', 'CLICK', { element_id: elementId, element_type: elementType, ...details }, page)
  }

  trackFilterChange(filterName, filterValue, page) {
    this.track('UI', 'FILTER_CHANGE', { filter_name: filterName, filter_value: filterValue }, page)
  }

  trackSearch(keyword, page) {
    this.track('UI', 'SEARCH', { keyword }, page)
  }

  trackDialogOpen(dialogId, page) {
    this.track('UI', 'DIALOG_OPEN', { dialog_id: dialogId }, page)
  }

  trackDialogClose(dialogId, page) {
    this.track('UI', 'DIALOG_CLOSE', { dialog_id: dialogId }, page)
  }

  trackDownload(fileType, page) {
    this.track('UI', 'DOWNLOAD', { file_type: fileType }, page)
  }

  trackPagination(pageNum, pageSize, page) {
    this.track('UI', 'PAGINATE', { page: pageNum, page_size: pageSize }, page)
  }

  trackSort(field, order, page) {
    this.track('UI', 'SORT', { sort_field: field, sort_order: order }, page)
  }

  trackExpand(rowId, page) {
    this.track('UI', 'EXPAND', { row_id: rowId }, page)
  }

  trackIndicatorSwitch(metricType, page) {
    this.track('UI', 'INDICATOR_SWITCH', { metric_type: metricType }, page)
  }

  trackLogout(page) {
    this.track('NAV', 'LOGOUT', {}, page)
  }

  // Category specific methods
  trackCategoryCreate(categoryData, page) {
    this.track('UI', 'CATEGORY_CREATE', categoryData, page)
  }

  trackCategoryEdit(categoryId, changes, page) {
    this.track('UI', 'CATEGORY_EDIT', { category_id: categoryId, changes }, page)
  }

  trackCategoryDelete(categoryId, page) {
    this.track('UI', 'CATEGORY_DELETE', { category_id: categoryId }, page)
  }

  // Report specific methods
  trackReportFilterChange(filterData, page) {
    this.track('UI', 'REPORT_FILTER_CHANGE', filterData, page)
  }

  trackReportQuery(params, page) {
    this.track('UI', 'REPORT_QUERY', params, page)
  }

  // Compare specific methods
  trackCompareFilterChange(filterData, page) {
    this.track('UI', 'COMPARE_FILTER_CHANGE', filterData, page)
  }

  trackProductSelect(productId, selectedCount, page) {
    this.track('UI', 'PRODUCT_SELECT', { product_id: productId, selected_count: selectedCount }, page)
  }

  // Chart specific methods
  trackChartViewDetail(chartType, page) {
    this.track('UI', 'CHART_VIEW_DETAIL', { chart_type: chartType }, page)
  }

  trackChartDownload(chartType, page) {
    this.track('UI', 'CHART_DOWNLOAD', { chart_type: chartType }, page)
  }

  destroy() {
    if (this.timer) {
      clearInterval(this.timer)
    }
    this._flushBeacon()
  }
}

// Export singleton instance
export const behaviorTracker = new BehaviorTracker()
export default behaviorTracker
