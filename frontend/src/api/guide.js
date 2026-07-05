import request from '../utils/request'

// 查询接口（所有用户）
export function getGuideList() {
  return request.get('/guide')
}

export function getGuideItem(itemId) {
  return request.get(`/guide/items/${itemId}`)
}

// 管理接口（仅HR）
export function getGuideCategories() {
  return request.get('/guide/admin/categories')
}

export function createGuideCategory(data) {
  return request.post('/guide/admin/categories', data)
}

export function updateGuideCategory(categoryId, data) {
  return request.put(`/guide/admin/categories/${categoryId}`, data)
}

export function deleteGuideCategory(categoryId) {
  return request.delete(`/guide/admin/categories/${categoryId}`)
}

export function createGuideItem(categoryId, data) {
  return request.post(`/guide/admin/categories/${categoryId}/items`, data)
}

export function updateGuideItem(itemId, data) {
  return request.put(`/guide/admin/items/${itemId}`, data)
}

export function deleteGuideItem(itemId) {
  return request.delete(`/guide/admin/items/${itemId}`)
}

export function batchImportGuideItems(items) {
  return request.post('/guide/admin/items/batch', { items })
}
