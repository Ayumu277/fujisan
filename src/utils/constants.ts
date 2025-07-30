// アプリケーション定数

export const APP_NAME = 'ABDS System';
export const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';

export const ROUTES = {
  HOME: '/',
  ABOUT: '/about',
  LOGIN: '/login',
} as const;