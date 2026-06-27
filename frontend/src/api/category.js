import api from './auth'

export const categoryApi = {
  getCategories() {
    return api.get('/categories')
  },
  getLevelOneCategories() {
    return api.get('/categories/level-one')
  },
  getLevelTwoCategories(parentId) {
    return api.get(`/categories/level-two/${parentId}`)
  },
  createCategory(data) {
    return api.post('/categories', data)
  },
  updateCategory(id, data) {
    return api.put(`/categories/${id}`, data)
  },
  deleteCategory(id) {
    return api.delete(`/categories/${id}`)
  },
  getProductCategories(productId) {
    return api.get(`/categories/product/${productId}`)
  },
  setProductCategories(productId, categoryIds) {
    return api.post(`/categories/product/${productId}`, { category_ids: categoryIds })
  }
}