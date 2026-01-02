/**
 * Radiology Assistant API Client
 */

// Auto-detect API base URL:
// - Production: Same origin (empty string uses relative paths)
// - Development: localhost:8000
const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';
const API_BASE = isProduction ? '' : 'http://localhost:8000';

class RadiologyAPI {
  constructor() {
    this.token = localStorage.getItem('auth_token');
  }

  setToken(token) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('auth_token');
  }

  getHeaders() {
    const headers = { 'Accept': 'application/json' };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
      ...options,
      headers: { ...this.getHeaders(), ...options.headers }
    };

    try {
      const response = await fetch(url, config);
      
      if (response.status === 401) {
        this.clearToken();
        window.location.href = 'index.html';
        throw new Error('Session expired');
      }

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Request failed');
      }
      
      return data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // Auth
  async login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${API_BASE}/api/auth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Login failed');
    }

    this.setToken(data.access_token);
    return data;
  }

  async signup(username, password, fullName = '', email = '', role = 'user') {
    const response = await fetch(`${API_BASE}/api/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username,
        password,
        full_name: fullName || username,
        email: email || null,
        role
      })
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Signup failed');
    }

    // Note: Signup does NOT return a token - user must verify email first
    // Token is returned after email verification
    return data;
  }

  async getCurrentUser() {
    return this.request('/api/auth/me');
  }

  logout() {
    this.clearToken();
    window.location.href = 'index.html';
  }

  // Health
  async healthCheck() {
    return this.request('/health');
  }

  // Analysis
  async analyzeDicom(files) {
    const formData = new FormData();
    for (const file of files) {
      formData.append('files', file);
    }

    const response = await fetch(`${API_BASE}/api/analyze`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.token}` },
      body: formData
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Analysis failed');
    }
    
    return data;
  }

  async uploadDicom(files) {
    const formData = new FormData();
    for (const file of files) {
      formData.append('files', file);
    }

    const response = await fetch(`${API_BASE}/api/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.token}` },
      body: formData
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'Upload failed');
    }
    
    return data;
  }

  async analyzeStudy(studyId) {
    return this.request(`/api/analyze/${studyId}`, { method: 'POST' });
  }

  async listStudies() {
    return this.request('/api/studies');
  }

  async deleteStudy(studyId) {
    return this.request(`/api/study/${studyId}`, { method: 'DELETE' });
  }
}

// Global instance
const api = new RadiologyAPI();

