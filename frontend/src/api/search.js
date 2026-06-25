import request from '../utils/request'

export function searchDocuments(params) {
  return request.get('/search', { params })
}
