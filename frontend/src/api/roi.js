import request from '../utils/request'

export function getRoiReport() {
  return request.get('/roi')
}
