"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { MyAssistant } from '@/components/MyAssistant';
import { jwtDecode } from 'jwt-decode';
import { getApiUrl } from '@/lib/utils';

// --- Constants & Types ---
const API_URL = getApiUrl();
const TOKEN_REFRESH_THRESHOLD = 5 * 60; // 5 minutes
const CHAT_ID_STORAGE_KEY = 'active_chat_id'; // LocalStorage key for chat ID

interface JWTPayload {
  exp?: number;
  type?: string;
  [key: string]: any;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface ChatIdResponse {
  active_chat_id: string;
}

interface ChatHistoryResponse {
  history: any[];
}

// --- Token Manager ---
const TokenManager = {
  getAccessToken: () => localStorage.getItem('token'),
  getRefreshToken: () => localStorage.getItem('refresh_token'),
  setTokens: (accessToken: string, refreshToken: string) => {
    localStorage.setItem('token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  },
  clearTokens: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem(CHAT_ID_STORAGE_KEY);
  },
  hasValidTokens: () => !!(localStorage.getItem('token') && localStorage.getItem('refresh_token')),
};

// --- Main Dashboard Component ---
export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [chatId, setChatId] = useState<string | null>(null);
  const [initialMessages, setInitialMessages] = useState<any[]>([]);
  const router = useRouter();

  // --- Helper: Check token expiry ---
  const isTokenExpiringSoon = (token: string): boolean => {
    try {
      const decoded = jwtDecode<JWTPayload>(token);
      if (!decoded.exp) return false;
      const currentTime = Math.floor(Date.now() / 1000);
      return decoded.exp - currentTime < TOKEN_REFRESH_THRESHOLD;
    } catch (error) {
      console.error("Error decoding token:", error);
      return false;
    }
  };

  // --- Helper: Refresh tokens ---
  const refreshTokens = async (): Promise<{ accessToken: string; refreshToken: string }> => {
    const refreshToken = TokenManager.getRefreshToken();
    if (!refreshToken) throw new Error('No refresh token available');

    const response = await fetch(`${API_URL}/api/auth/refresh`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${refreshToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) throw new Error('Failed to refresh token');
    const data: TokenResponse = await response.json();

    if (!data.access_token || !data.refresh_token) throw new Error('Invalid token response');
    TokenManager.setTokens(data.access_token, data.refresh_token);

    return { accessToken: data.access_token, refreshToken: data.refresh_token };
  };

  // --- Helper: Ensure we always have a valid access token ---
  const getValidToken = async (): Promise<string | null> => {
    if (!TokenManager.hasValidTokens()) return null;
    let token = TokenManager.getAccessToken();
    if (token && isTokenExpiringSoon(token)) {
      try {
        const { accessToken } = await refreshTokens();
        return accessToken;
      } catch {
        TokenManager.clearTokens();
        return null;
      }
    }
    return token;
  };

  // --- Helper: Get or create chat ID ---
  const getActiveChatId = async (token: string): Promise<string | null> => {
    const storedChatId = localStorage.getItem(CHAT_ID_STORAGE_KEY);
    if (storedChatId) return storedChatId;

    try {
      const response = await fetch(`${API_URL}/api/auth/set-chat-id`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('API failed to create new chat ID');
      const data: ChatIdResponse = await response.json();
      localStorage.setItem(CHAT_ID_STORAGE_KEY, data.active_chat_id);
      return data.active_chat_id;
    } catch (error) {
      console.error("Error setting chat ID:", error);
      return null;
    }
  };

  // --- Helper: Fetch chat history ---
  const fetchChatHistory = async (id: string, token: string) => {
    try {
      const response = await fetch(`${API_URL}/api/virtual-ta/chat/history`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Chat-ID': id,
        },
      });
      if (response.ok) {
        const data: ChatHistoryResponse = await response.json();
        setInitialMessages(data.history || []);
      } else {
        // if chat history fetch fails, reset chatId
        localStorage.removeItem(CHAT_ID_STORAGE_KEY);
        window.location.reload();
      }
    } catch (error) {
      console.error('Error fetching chat history:', error);
    }
  };

  // --- Main initialization effect ---
  useEffect(() => {
    const initialize = async () => {
      try {
        const token = await getValidToken();
        if (!token) {
          router.push('/');
          return;
        }

        const activeChatId = await getActiveChatId(token);
        if (!activeChatId) {
          setLoading(false);
          return;
        }

        setChatId(activeChatId);
        await fetchChatHistory(activeChatId, token);
      } catch (err) {
        console.error("Error initializing dashboard:", err);
        TokenManager.clearTokens();
        router.push('/');
      } finally {
        setLoading(false);
      }
    };

    initialize();

    // periodic background refresh check
    const refreshInterval = setInterval(() => {
      const token = TokenManager.getAccessToken();
      if (token && isTokenExpiringSoon(token)) {
        refreshTokens().catch(() => {
          TokenManager.clearTokens();
          router.push('/');
        });
      }
    }, 60000);

    return () => clearInterval(refreshInterval);
  }, [router]);

  // --- Loading spinner ---
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-600"></div>
      </div>
    );
  }

  // --- Render assistant ---
  return (
    <main className="flex flex-col h-[calc(100vh-64px)]">
      <div className="flex-1">
        <MyAssistant chatId={chatId} initialMessages={initialMessages} />
      </div>
    </main>
  );
}
