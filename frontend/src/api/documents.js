import request from '../utils/request'

export function getDocuments(params) {
  return request.get('/documents', { params })
}

export function getDocument(docId) {
  return request.get(`/documents/${docId}`)
}

export function createDocument(formData) {
  return request.post('/documents', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
}

export function updateDocument(docId, formData) {
  return request.put(`/documents/${docId}`, formData, { headers: { 'Content-Type': 'multipart/form-data' } })
}

export function deleteDocument(docId) {
  return request.delete(`/documents/${docId}`)
}

export function publishDocument(docId) {
  return request.post(`/documents/${docId}/publish`)
}

export function archiveDocument(docId) {
  return request.post(`/documents/${docId}/archive`)
}

export function unarchiveDocument(docId) {
  return request.post(`/documents/${docId}/unarchive`)
}

export function classifyDocument(formData) {
  return request.post('/documents/classify', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
}

export function downloadDocument(docId) {
  return request.get(`/documents/${docId}/download`, { responseType: 'blob' })
}

export function getDocumentChunks(docId) {
  return request.get(`/documents/${docId}/chunks`)
}

export function getDocumentVersions(docId) {
  return request.get(`/documents/${docId}/versions`)
}
