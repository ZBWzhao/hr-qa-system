import request from '../utils/request'

export function getOnboarding() {
  return request.get('/onboarding')
}

export function markDocRead(docId) {
  return request.put(`/onboarding/checklist/${docId}`)
}
