import axios, { AxiosResponse } from 'axios';
import { 
  ChatResponse, 
  Product, 
  User, 
  LoginCredentials, 
  RegisterData,
  ApiResponse 
} from '../types';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      // You might want to redirect to login page here
    }
    return Promise.reject(error);
  }
);

export class ApiService {
  // Auth endpoints
  static async login(credentials: LoginCredentials): Promise<{ access_token: string; token_type: string }> {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  }

  static async register(userData: RegisterData): Promise<User> {
    const response = await api.post('/auth/register', userData);
    return response.data;
  }

  static async getCurrentUser(): Promise<User> {
    const response = await api.get('/auth/me');
    return response.data;
  }

  // Chat endpoints
  static async sendMessage(message: string, sessionId?: string): Promise<ChatResponse> {
    const response = await api.post('/chat/message', {
      message,
      session_id: sessionId,
    });
    return response.data;
  }

  static async getChatHistory(sessionId: string, limit = 20): Promise<any[]> {
    const response = await api.get(`/chat/history/${sessionId}?limit=${limit}`);
    return response.data;
  }

  static async getChatSessions(): Promise<any[]> {
    const response = await api.get('/chat/sessions');
    return response.data;
  }

  // Product endpoints
  static async getProducts(params?: {
    category?: string;
    color?: string;
    brand?: string;
    min_price?: number;
    max_price?: number;
    limit?: number;
    offset?: number;
  }): Promise<Product[]> {
    const response = await api.get('/products/', { params });
    return response.data;
  }

  static async searchProducts(params: {
    q: string;
    category?: string;
    color?: string;
    brand?: string;
    min_price?: number;
    max_price?: number;
    limit?: number;
  }): Promise<Product[]> {
    const response = await api.get('/products/search', { params });
    return response.data;
  }

  static async getProduct(id: number): Promise<Product> {
    const response = await api.get(`/products/${id}`);
    return response.data;
  }

  static async getCategories(): Promise<string[]> {
    const response = await api.get('/products/categories/list');
    return response.data;
  }

  static async getBrands(): Promise<string[]> {
    const response = await api.get('/products/brands/list');
    return response.data;
  }

  // Health check
  static async healthCheck(): Promise<any> {
    const response = await api.get('/api/health');
    return response.data;
  }

  static async getAppInfo(): Promise<any> {
    const response = await api.get('/api/info');
    return response.data;
  }
}

export default ApiService;
