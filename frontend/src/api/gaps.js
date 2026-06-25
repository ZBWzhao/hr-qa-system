import request from '../utils/request'

export function getGaps(params) {
  return request.get('/gaps', { params })
}

export function getGapStats() {
  return request.get('/gaps/stats')
}

export function resolveGap(missId, docId) {
  return request.put(`/gaps/${missId}/resolve`, null, { params: { doc_id: docId } })
}
