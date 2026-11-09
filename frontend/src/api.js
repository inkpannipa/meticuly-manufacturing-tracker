const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    headers: {'Content-Type': 'application/json', ...(options.headers || {})}, ...options,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || 'Something went wrong')
  }
  return response.json()
}

export const api = {
  bootstrap: () => Promise.all([request('/api/dashboard'), request('/api/orders'), request('/api/steps'), request('/api/resources')]),
  createOrder: (data) => request('/api/orders', {method: 'POST', body: JSON.stringify(data)}),
  advance: (id, data) => request(`/api/orders/${id}/advance`, {method: 'POST', body: JSON.stringify(data)}),
}

