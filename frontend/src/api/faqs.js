import request from '../utils/request'

export function getFaqs(params) {
  return request.get('/faqs', { params })
}

export function getAllFaqs(params) {
  return request.get('/faqs/all', { params })
}

export function getFaq(faqId) {
  return request.get(`/faqs/${faqId}`)
}

export function createFaq(data) {
  return request.post('/faqs', data)
}

export function updateFaq(faqId, data) {
  return request.put(`/faqs/${faqId}`, data)
}

export function deleteFaq(faqId) {
  return request.delete(`/faqs/${faqId}`)
}

export function generateKeywords(data) {
  return request.post('/faqs/generate-keywords', data)
}
