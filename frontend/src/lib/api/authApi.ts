import { apiClient } from '@/lib/api/client';

export type Role = 'HR_ADMIN' | 'EMPLOYEE';

export interface LoginResponse {
  role: Role;
  user_id: string;
}

export interface MeResponse {
  role: Role;
  user_id: string;
  name: string;
  email: string;
}

/** Matches backend/app/core/errors.py's centralized error contract. */
export interface ApiErrorBody {
  status: 'error';
  code: string;
  message: string;
  timestamp: string;
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>('/api/auth/login', { email, password });
  return response.data;
}

export async function logout(): Promise<void> {
  await apiClient.post('/api/auth/logout');
}

export async function getMe(): Promise<MeResponse> {
  const response = await apiClient.get<MeResponse>('/api/auth/me', { timeout: 8000 });
  return response.data;
}
