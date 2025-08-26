export interface User {
  id: number;
  email: string;
  username: string;
  created_at: string;
  is_active: boolean;
}

export interface Product {
  id: number;
  name: string;
  description: string;
  price: number;
  category: string;
  color?: string;
  size?: string;
  brand?: string;
  image_url?: string;
  stock_quantity: number;
  tags?: any;
  created_at: string;
}

export interface ChatMessage {
  type: 'user' | 'assistant';
  content: string;
  timestamp: string;
  intent?: string;
  products?: Product[];
  orders?: any[];
}

export interface ChatResponse {
  response: string;
  intent: string;
  session_id: string;
  products?: Product[];
  orders?: any[];
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}
