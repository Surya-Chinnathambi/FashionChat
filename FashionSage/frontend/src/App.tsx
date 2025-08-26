import React, { useState, useEffect } from 'react';
import ChatWidget from './components/ChatWidget';
import LoginForm from './components/LoginForm';
import { ApiService } from './services/api';
import { User, LoginCredentials, RegisterData } from './types';

const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showLoginForm, setShowLoginForm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [appInfo, setAppInfo] = useState<any>(null);
  const [healthStatus, setHealthStatus] = useState<any>(null);

  // Initialize app and check authentication
  useEffect(() => {
    const initializeApp = async () => {
      // Load app info
      try {
        const info = await ApiService.getAppInfo();
        setAppInfo(info);
      } catch (error) {
        console.error('Failed to load app info:', error);
      }

      // Check health
      try {
        const health = await ApiService.healthCheck();
        setHealthStatus(health);
      } catch (error) {
        console.error('Health check failed:', error);
      }

      // Check for existing token
      const token = localStorage.getItem('token');
      const userData = localStorage.getItem('user');

      if (token && userData) {
        try {
          const parsedUser = JSON.parse(userData);
          setUser(parsedUser);
          setIsAuthenticated(true);
          
          // Verify token is still valid
          const currentUser = await ApiService.getCurrentUser();
          setUser(currentUser);
        } catch (error) {
          // Token is invalid, clear it
          localStorage.removeItem('token');
          localStorage.removeItem('user');
        }
      }
    };

    initializeApp();
  }, []);

  const handleLogin = async (credentials: LoginCredentials) => {
    setIsLoading(true);
    try {
      const response = await ApiService.login(credentials);
      localStorage.setItem('token', response.access_token);
      
      const currentUser = await ApiService.getCurrentUser();
      setUser(currentUser);
      setIsAuthenticated(true);
      localStorage.setItem('user', JSON.stringify(currentUser));
      
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (userData: RegisterData) => {
    setIsLoading(true);
    try {
      await ApiService.register(userData);
      
      // Auto-login after registration
      await handleLogin({
        email: userData.email,
        password: userData.password,
      });
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                <i className="fas fa-tshirt text-white"></i>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Fashion Store</h1>
                <p className="text-xs text-gray-500">AI-Powered Shopping Assistant</p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {isAuthenticated ? (
                <div className="flex items-center space-x-3">
                  <div className="text-sm">
                    <p className="font-medium text-gray-900">Welcome, {user?.username}!</p>
                    <p className="text-gray-500">{user?.email}</p>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-800 px-3 py-2 rounded-lg text-sm transition-colors"
                  >
                    <i className="fas fa-sign-out-alt mr-1"></i>
                    Logout
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setShowLoginForm(true)}
                  className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm transition-colors"
                >
                  <i className="fas fa-user mr-1"></i>
                  Sign In
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center mb-8">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Your AI Fashion Assistant
          </h2>
          <p className="text-lg text-gray-600 mb-6">
            Ask me anything about our products, get personalized recommendations, 
            or track your orders - I'm here to help!
          </p>
          
          {/* Feature highlights */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
            <div className="bg-white rounded-xl p-6 shadow-sm border hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <i className="fas fa-search text-blue-500 text-xl"></i>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Smart Product Search</h3>
              <p className="text-gray-600 text-sm">
                Find exactly what you're looking for with our AI-powered vector search
              </p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <i className="fas fa-heart text-green-500 text-xl"></i>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Personalized Recommendations</h3>
              <p className="text-gray-600 text-sm">
                Get tailored suggestions based on your style preferences and history
              </p>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-sm border hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <i className="fas fa-box text-purple-500 text-xl"></i>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Order Tracking</h3>
              <p className="text-gray-600 text-sm">
                Track your orders and get updates on delivery status instantly
              </p>
            </div>
          </div>
        </div>

        {/* System Status */}
        {healthStatus && (
          <div className="bg-white rounded-xl p-4 shadow-sm border mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${
                  healthStatus.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                }`}></div>
                <span className="text-sm font-medium text-gray-700">System Status</span>
              </div>
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                <span>Products: {healthStatus.chroma_products}</span>
                <span>Database: {healthStatus.database}</span>
                <span>AI: {healthStatus.openrouter_configured ? 'Ready' : 'Not configured'}</span>
              </div>
            </div>
          </div>
        )}

        {/* Welcome Instructions */}
        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">How to Get Started</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <div className="flex items-start space-x-3">
                <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold">1</div>
                <p className="text-sm text-gray-700">Click the chat button in the bottom right corner</p>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold">2</div>
                <p className="text-sm text-gray-700">Ask about products: "Show me summer dresses" or "Find black shoes"</p>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-start space-x-3">
                <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold">3</div>
                <p className="text-sm text-gray-700">Sign in to track orders: "Where is my order?"</p>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold">4</div>
                <p className="text-sm text-gray-700">Get style advice: "What goes well with this outfit?"</p>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Chat Widget */}
      <ChatWidget 
        isAuthenticated={isAuthenticated}
        onLoginClick={() => setShowLoginForm(true)}
      />

      {/* Login Form Modal */}
      {showLoginForm && (
        <LoginForm
          onLogin={handleLogin}
          onRegister={handleRegister}
          isLoading={isLoading}
          onClose={() => setShowLoginForm(false)}
        />
      )}
    </div>
  );
};

export default App;
