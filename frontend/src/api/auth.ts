import axios from 'axios';

const API_BASE = '/api';

export const apiClient = axios.create({
    baseURL: API_BASE,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Storage keys
const ACCESS_TOKEN_KEY = 'careerflow_access_token';
const REFRESH_TOKEN_KEY = 'careerflow_refresh_token';
const USER_KEY = 'careerflow_user';

export const getStoredTokens = () => ({
    access: localStorage.getItem(ACCESS_TOKEN_KEY),
    refresh: localStorage.getItem(REFRESH_TOKEN_KEY),
});

export const storeTokens = (access: string, refresh: string) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
};

export const clearTokens = () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
};

export const storeUser = (user: any) => {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
};

export const getStoredUser = () => {
    const data = localStorage.getItem(USER_KEY);
    return data ? JSON.parse(data) : null;
};

// Request interceptor to attach JWT Access Token
apiClient.interceptors.request.use((config) => {
    const { access } = getStoredTokens();
    if (access && config.headers) {
        config.headers.Authorization = `Bearer ${access}`;
    }
    return config;
});

// Response interceptor to auto-refresh token on 401
apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            const { refresh } = getStoredTokens();
            if (refresh) {
                try {
                    const res = await axios.post(`${API_BASE}/auth/token/refresh/`, {
                        refresh,
                    });
                    const newAccess = res.data.access;
                    localStorage.setItem(ACCESS_TOKEN_KEY, newAccess);
                    originalRequest.headers.Authorization = `Bearer ${newAccess}`;
                    return apiClient(originalRequest);
                } catch (refreshErr) {
                    clearTokens();
                }
            }
        }
        return Promise.reject(error);
    }
);

export async function apiRegister(data: {
    email: string;
    password: string;
    full_name?: string;
    role?: string;
    confirm_password?: string;
}) {
    const response = await apiClient.post('/auth/register/', data);
    if (response.data?.tokens) {
        storeTokens(response.data.tokens.access, response.data.tokens.refresh);
        if (response.data.user) {
            storeUser(response.data.user);
        }
    }
    return response.data;
}

export async function apiLogin(email: string, password: string) {
    const response = await apiClient.post('/auth/login/', { email, password });
    if (response.data) {
        storeTokens(response.data.access, response.data.refresh);
        if (response.data.user) {
            storeUser(response.data.user);
        }
    }
    return response.data;
}

export async function apiLogout() {
    const { refresh } = getStoredTokens();
    if (refresh) {
        try {
            await apiClient.post('/auth/logout/', { refresh });
        } catch {
            // Best effort logout
        }
    }
    clearTokens();
}

export async function apiGetCurrentUser() {
    const response = await apiClient.get('/auth/me/');
    return response.data;
}