/**
 * API service for communicating with backend
 */
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const apiService = {
  // Patients
  patients: {
    list: () => api.get('/patients'),
    get: (patientId: string) => api.get(`/patients/${patientId}`),
    create: (data: any) => api.post('/patients', data),
    update: (patientId: string, data: any) => api.put(`/patients/${patientId}`, data),
    delete: (patientId: string) => api.delete(`/patients/${patientId}`),
  },
  
  // Surgeries
  surgeries: {
    list: (params?: any) => api.get('/surgeries', { params }),
    get: (surgeryId: string) => api.get(`/surgeries/${surgeryId}`),
    create: (data: any) => api.post('/surgeries', data),
    update: (surgeryId: string, data: any) => api.put(`/surgeries/${surgeryId}`, data),
    delete: (surgeryId: string) => api.delete(`/surgeries/${surgeryId}`),
  },
  
  // Reports
  reports: {
    summary: () => api.get('/reports/summary'),
    complications: () => api.get('/reports/complications'),
    trends: (days?: number) => api.get('/reports/trends', { params: { days } }),
    surgeonPerformance: () => api.get('/reports/surgeon-performance'),
  },
}

// Export both the service object and raw axios instance
export default api